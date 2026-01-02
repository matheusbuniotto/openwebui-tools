"""
title: Conselho de LLMs
author: matheusbuniotto
funding_url: https://github.com/matheusbuniotto/openwebui-tools
version: 0.2.1
license: MIT
"""

import os
import asyncio
import re
from typing import List, Dict, Any, Tuple, Optional
from pydantic import BaseModel, Field
import requests


MODELOS_PADRAO = "openai/gpt-4.1,openai/gpt-4o-mini,google/gemini-2.5-flash"


class Tools:
    class Valves(BaseModel):
        openwebui_base_url: str = Field(
            default="",
            description="URL base da API do OpenWebUI. Deixe vazio para auto-detectar (tenta localhost:3000, depois host.docker.internal:3000).",
        )
        openwebui_api_key: str = Field(
            default="",
            description="Chave de API do OpenWebUI. Deixe vazio para auto-detectar da sessao ou variavel OPENWEBUI_API_KEY.",
        )
        council_models: str = Field(
            default=MODELOS_PADRAO,
            description="IDs dos modelos separados por virgula (ex: 'llama3:latest,gpt-4o') ou 'all' para usar todos os modelos disponiveis (limitado por max_models).",
        )
        chairperson_model: str = Field(
            default="",
            description="ID do modelo Presidente que sintetiza a resposta final. Se vazio, usa o primeiro modelo do conselho.",
        )
        max_models: int = Field(
            default=5,
            description="Numero maximo de modelos ao usar 'all'. Previne custos excessivos.",
        )
        timeout: int = Field(
            default=60, description="Timeout em segundos para requisicoes aos modelos."
        )

    def __init__(self):
        self.valves = self.Valves()
        self._resolved_api_key: Optional[str] = None
        self._resolved_base_url: Optional[str] = None

    def _resolve_api_key(self, __user__: Optional[dict] = None) -> Optional[str]:
        """
        Resolve a chave de API na ordem de prioridade:
        1. Token do dict __user__ (passado pelo OpenWebUI)
        2. Variavel de ambiente OPENWEBUI_API_KEY
        3. Configuracao do Valve
        """
        if __user__:
            token = __user__.get("token") or __user__.get("api_key")
            if token:
                return token

        env_key = os.environ.get("OPENWEBUI_API_KEY")
        if env_key:
            return env_key

        if self.valves.openwebui_api_key:
            return self.valves.openwebui_api_key

        return None

    def _resolve_base_url(self) -> str:
        """
        Resolve a URL base na ordem de prioridade:
        1. Configuracao do Valve (se definida)
        2. Variavel de ambiente OPENWEBUI_BASE_URL
        3. Auto-detectar (localhost primeiro, depois Docker interno)
        """
        if self.valves.openwebui_base_url:
            return self.valves.openwebui_base_url

        env_url = os.environ.get("OPENWEBUI_BASE_URL")
        if env_url:
            return env_url

        localhost_url = "http://localhost:3000/api"
        docker_url = "http://host.docker.internal:3000/api"

        try:
            response = requests.get(f"{localhost_url}/models", timeout=2)
            if response.status_code in [200, 401, 403]:
                return localhost_url
        except Exception:
            pass

        return docker_url

    async def _emit_status(
        self,
        event_emitter: Any,
        level: str,
        message: str,
        done: bool,
    ):
        """
        Emite atualizacoes de status para a interface do OpenWebUI.
        """
        if event_emitter:
            await event_emitter(
                {
                    "type": "status",
                    "data": {
                        "status": "complete" if done else "in_progress",
                        "level": level,
                        "description": message,
                        "done": done,
                    },
                }
            )

    def _query_model_sync(
        self, model: str, messages: List[Dict[str, Any]], api_key: str, base_url: str
    ) -> Optional[Dict[str, Any]]:
        """
        Helper sincrono para consultar um modelo via API do OpenWebUI.
        """
        url = f"{base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": messages,
        }

        try:
            response = requests.post(
                url, headers=headers, json=payload, timeout=self.valves.timeout
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]
        except Exception as e:
            print(f"Erro ao consultar modelo {model}: {e}")
            return {"error": str(e)}

    async def _query_model_async(
        self, model: str, messages: List[Dict[str, Any]], api_key: str, base_url: str
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        Wrapper assincrono para consultar um modelo.
        """
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, self._query_model_sync, model, messages, api_key, base_url
        )
        return model, result

    def _parse_ranking_from_text(self, ranking_text: str) -> List[str]:
        """
        Extrai a lista de ranking da resposta de texto do modelo.
        Procura por 'RANKING FINAL:' seguido de '1. Resposta X'.
        """
        if "RANKING FINAL:" in ranking_text:
            parts = ranking_text.split("RANKING FINAL:")
            if len(parts) >= 2:
                ranking_section = parts[1]
                numbered_matches = re.findall(
                    r"\d+\.\s*Resposta [A-Z]", ranking_section
                )
                if numbered_matches:
                    return [
                        re.search(r"Resposta [A-Z]", m).group()
                        for m in numbered_matches
                    ]

                matches = re.findall(r"Resposta [A-Z]", ranking_section)
                return matches

        matches = re.findall(r"Resposta [A-Z]", ranking_text)
        return matches

    def _get_available_models(self, api_key: str, base_url: str) -> List[str]:
        """
        Busca a lista de IDs de modelos disponiveis da API do OpenWebUI.
        """
        url = f"{base_url}/models"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.get(url, headers=headers, timeout=self.valves.timeout)
            response.raise_for_status()
            data = response.json()
            return [model["id"] for model in data.get("data", [])]
        except Exception as e:
            print(f"Erro ao buscar modelos disponiveis: {e}")
            return []

    async def consultar_conselho(
        self,
        topico: str,
        __user__: Optional[dict] = None,
        __event_emitter__: Any = None,
    ) -> str:
        """
        Orquestra uma reuniao de conselho em 3 etapas:
        1. Conselho fornece respostas individuais.
        2. Conselho classifica as respostas dos pares.
        3. Presidente sintetiza a resposta final.
        """
        api_key = self._resolve_api_key(__user__)
        base_url = self._resolve_base_url()

        if not api_key:
            await self._emit_status(
                __event_emitter__,
                "error",
                "Chave de API nao encontrada. Defina OPENWEBUI_API_KEY ou configure nos Valves.",
                True,
            )
            return "Erro: Chave de API nao encontrada. Defina a variavel de ambiente OPENWEBUI_API_KEY ou configure 'openwebui_api_key' nas configuracoes da ferramenta."

        available_models = await asyncio.get_running_loop().run_in_executor(
            None, self._get_available_models, api_key, base_url
        )

        configured_models_raw = self.valves.council_models.lower().strip()

        target_models = []
        if configured_models_raw == "all":
            if available_models:
                target_models = available_models[: self.valves.max_models]
                if len(available_models) > self.valves.max_models:
                    await self._emit_status(
                        __event_emitter__,
                        "info",
                        f"Limitando conselho a {self.valves.max_models} modelos (de {len(available_models)} disponiveis).",
                        False,
                    )
            else:
                return "Erro: 'council_models' definido como 'all', mas nao foi possivel buscar modelos disponiveis da API."
        else:
            requested_models = [
                m.strip() for m in self.valves.council_models.split(",") if m.strip()
            ]

            if available_models:
                missing_models = []
                for m in requested_models:
                    if m in available_models:
                        target_models.append(m)
                    else:
                        missing_models.append(m)

                if missing_models:
                    warning_msg = f"Aviso: Os seguintes modelos nao foram encontrados e serao ignorados: {', '.join(missing_models)}"
                    await self._emit_status(
                        __event_emitter__, "info", warning_msg, False
                    )

                if not target_models:
                    return f"Erro: Nenhum dos modelos solicitados ({', '.join(requested_models)}) esta disponivel."
            else:
                await self._emit_status(
                    __event_emitter__,
                    "info",
                    "Nao foi possivel verificar modelos com a API, prosseguindo com a lista configurada.",
                    False,
                )
                target_models = requested_models

        council_models_list = target_models

        if not council_models_list:
            return "Erro: Nenhum modelo do conselho configurado ou encontrado."

        chairperson = self.valves.chairperson_model
        if not chairperson:
            chairperson = council_models_list[0]

        if available_models and chairperson not in available_models:
            await self._emit_status(
                __event_emitter__,
                "info",
                f"Aviso: Modelo presidente '{chairperson}' nao encontrado nos modelos disponiveis. Tentando mesmo assim...",
                False,
            )

        # --- Etapa 1: Coletar Respostas ---
        await self._emit_status(
            __event_emitter__,
            "info",
            f"Etapa 1: Consultando {len(council_models_list)} membros do conselho: {', '.join(council_models_list)}",
            False,
        )

        stage1_messages = [{"role": "user", "content": topico}]
        tasks = [
            self._query_model_async(model, stage1_messages, api_key, base_url)
            for model in council_models_list
        ]

        stage1_results_raw = await asyncio.gather(*tasks)

        valid_responses = []
        errors = []
        for model, response in stage1_results_raw:
            if response and "error" not in response:
                content = response.get("content", "")
                if content:
                    valid_responses.append({"model": model, "response": content})
            elif response and "error" in response:
                errors.append(f"{model}: {response['error']}")

        if not valid_responses:
            error_details = "; ".join(errors) if errors else "Erro desconhecido"
            error_msg = f"Todos os modelos do conselho falharam. Erros: {error_details}"
            await self._emit_status(
                __event_emitter__, "error", f"Falha: {error_details[:100]}...", True
            )
            return f"Erro: Verifique sua URL base e chave de API do OpenWebUI. Detalhes: {error_msg}"

        # --- Etapa 2: Avaliacao entre Pares ---
        await self._emit_status(
            __event_emitter__,
            "info",
            "Etapa 2: Conselho esta avaliando as respostas dos colegas...",
            False,
        )

        labels = [chr(65 + i) for i in range(len(valid_responses))]

        responses_text = "\n\n".join(
            [
                f"Resposta {label}:\n{r['response']}"
                for label, r in zip(labels, valid_responses)
            ]
        )

        ranking_prompt = f"""Voce esta avaliando diferentes respostas para a seguinte pergunta:

Pergunta: {topico}

Aqui estao as respostas de diferentes modelos (anonimizadas):

{responses_text}

Sua tarefa:
1. Avaliar cada resposta individualmente (pontos fortes/fracos).
2. Fornecer um ranking final.

IMPORTANTE: Seu ranking final DEVE ser formatado EXATAMENTE assim:
- Comece com a linha "RANKING FINAL:" (tudo em maiusculas, com dois pontos)
- Depois liste as respostas da melhor para a pior como uma lista numerada
- Cada linha deve ser: numero, ponto, espaco, depois APENAS o rotulo da resposta (ex: "1. Resposta A")

RANKING FINAL:
1. Resposta [Rotulo]
2. Resposta [Rotulo]
...
"""
        ranking_messages = [{"role": "user", "content": ranking_prompt}]

        ranking_tasks = [
            self._query_model_async(model, ranking_messages, api_key, base_url)
            for model in council_models_list
        ]
        stage2_results_raw = await asyncio.gather(*ranking_tasks)

        rankings = []
        for model, response in stage2_results_raw:
            if response:
                content = response.get("content", "")
                parsed = self._parse_ranking_from_text(content)
                rankings.append(
                    {"model": model, "full_text": content, "parsed": parsed}
                )

        # --- Etapa 3: Sintese ---
        await self._emit_status(
            __event_emitter__,
            "info",
            "Etapa 3: Presidente esta sintetizando o resultado...",
            False,
        )

        stage1_summary = "\n\n".join(
            [
                f"Modelo: {r['model']}\nResposta: {r['response']}"
                for r in valid_responses
            ]
        )

        stage2_summary = "\n\n".join(
            [
                f"Modelo: {r['model']}\nRanking: {r.get('parsed', 'Nenhum ranking valido encontrado')}"
                for r in rankings
            ]
        )

        chairman_prompt = f"""Voce e o Presidente de um Conselho de LLMs.

Pergunta Original: {topico}

ETAPA 1 - Respostas Individuais:
{stage1_summary}

ETAPA 2 - Rankings dos Pares:
{stage2_summary}

Sua tarefa como Presidente e sintetizar uma unica resposta abrangente.
Considere os insights da Etapa 1 e o consenso (ou discordancia) da Etapa 2.
"""
        chairman_messages = [{"role": "user", "content": chairman_prompt}]

        _, final_response = await self._query_model_async(
            chairperson, chairman_messages, api_key, base_url
        )

        await self._emit_status(
            __event_emitter__, "info", "Reuniao do conselho encerrada.", True
        )

        # --- Construir Relatorio Detalhado ---

        report_parts = ["# Relatorio do Conselho de LLMs\n"]

        report_parts.append("## Etapa 1: Perspectivas Individuais")
        for r in valid_responses:
            report_parts.append(f"### {r['model']}\n{r['response']}\n")

        report_parts.append("\n## Etapa 2: Avaliacao e Ranking entre Pares")
        for r in rankings:
            report_parts.append(f"### Ranking de {r['model']}\n{r['full_text']}\n")

        if final_response:
            final_synthesis = final_response.get("content", "Erro: Sem conteudo.")
            report_parts.append(
                f"\n## Etapa 3: Sintese do Presidente ({chairperson})\n{final_synthesis}"
            )
        else:
            final_synthesis = "Erro: Presidente falhou ao sintetizar a resposta final."
            report_parts.append(
                f"\n## Etapa 3: Sintese do Presidente\n{final_synthesis}"
            )

        full_report = "\n".join(report_parts)

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "message",
                    "data": {"content": full_report},
                }
            )

        return full_report
