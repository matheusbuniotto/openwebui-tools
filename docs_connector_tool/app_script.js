/*
title: Google Docs Script Connector
author: matheusbuniotto
funding_url: 
version: 0.0.1
license: MIT
*/

/**
 * This script is designed to be deployed as a Google Apps Script Web App.
 * It receives a JSON payload with a filename and a list of replacements (things between {}),
 * creates a copy of the current document (template), performs the replacements,
 * and returns the URL of the new document.
 */
function doPost(e) {
    try {
        // 1. Receive data from OpenWebUI
        var data = JSON.parse(e.postData.contents);
        var newName = data.filename || "New Document";
        var replacements = data.replacements || {};

        // 2. Get the current file (Template) and make a copy
        var templateId = DocumentApp.getActiveDocument().getId();
        var templateFile = DriveApp.getFileById(templateId);
        var newFile = templateFile.makeCopy(newName);

        // 3. Open the copy for editing
        var newDoc = DocumentApp.openById(newFile.getId());
        var body = newDoc.getBody();

        // 4. Replace the text
        for (var key in replacements) {
            body.replaceText(key, replacements[key]);
        }

        newDoc.saveAndClose();

        // 5. Make the link accessible (Edit Link)
        // Optional: If you want it to be private, remove the line below,
        // but the user will have to be logged into the owner account to view it.
        newFile.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.EDIT);

        return ContentService.createTextOutput(JSON.stringify({
            "status": "success",
            "url": newFile.getUrl()
        })).setMimeType(ContentService.MimeType.JSON);

    } catch (error) {
        return ContentService.createTextOutput(JSON.stringify({
            "status": "error",
            "message": error.toString()
        })).setMimeType(ContentService.MimeType.JSON);
    }
}