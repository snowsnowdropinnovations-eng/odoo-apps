/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { HtmlField } from "@web_editor/js/backend/html_field";
import { preserveCursor } from "@web_editor/js/editor/odoo-editor/src/utils/utils";
import { ChatGPTAlternativesDialog } from '@web_editor/js/wysiwyg/widgets/chatgpt_alternatives_dialog';
import * as OdooEditorLib from "@web_editor/js/editor/odoo-editor/src/OdooEditor";

const closestElement = OdooEditorLib.closestElement;

patch(HtmlField.prototype, {
    setup() {
        super.setup();
        this.dialog = useService("dialog");
        this.notification = useService("notification");
    },

    mounted() {
        super.mounted?.();

//        setTimeout(() => {
//            const editable = this.el.querySelector(".note-editable, [contenteditable='true']");
//            if (!editable || editable.querySelector("#chatgpt-btn")) return;
//
//            const btn = document.createElement("button");
//            btn.id = "chatgpt-btn";
//            btn.className = "btn btn-light editor-ignore";
//            btn.title = "Generate or transform content with AI";
//            btn.innerHTML = `<span class="fa fa-magic"></span>`;
//            btn.style.position = "absolute";
//            btn.style.top = "6px";
//            btn.style.right = "6px";
//            btn.style.zIndex = "10";
//
//            editable.style.position = "relative";
//            editable.appendChild(btn);
//
//            btn.addEventListener("click", (ev) => this._onAIClick(ev));
//        }, 500);
    },

    _getEditor() {
        return this.wysiwyg?.odooEditor || null;
    },


    openChatGPTDialog(editor, mode = "prompt") {
        const restore = preserveCursor(editor.document);

        const params = {
            insert: (content) => {
                editor.historyPauseSteps();
                const insertedNodes = editor.execCommand("insert", content);
                editor.historyUnpauseSteps();
                editor.historyStep();

                // highlight newly inserted content (optional visual cue)
                const start = insertedNodes?.length && closestElement(insertedNodes[0]);
                const end = insertedNodes?.length && closestElement(insertedNodes[insertedNodes.length - 1]);
                if (start && end) {
                    const div = document.createElement("div");
                    div.classList.add("o-chatgpt-content");
                    const FRAME_PADDING = 3;
                    div.style.position = "absolute";
                    div.style.left = `${start.offsetLeft - FRAME_PADDING}px`;
                    div.style.top = `${start.offsetTop - FRAME_PADDING}px`;
                    div.style.width = `${Math.max(start.offsetWidth, end.offsetWidth) + FRAME_PADDING * 2}px`;
                    div.style.height = `${end.offsetTop + end.offsetHeight - start.offsetTop + FRAME_PADDING * 2}px`;
                    editor.editable.parentElement.prepend(div);
                    setTimeout(() => div.remove(), 2000);
                }
            },
        };

        if (mode === "alternatives") {
            params.originalText = editor.document.getSelection().toString() || "";
        }

        this.env.services.dialog.add(
            ChatGPTAlternativesDialog,
            params,
            { onClose: restore },
        );

        //Remove toolbar
        setTimeout(() => {
            const toolbar = document.getElementById("toolbar");
            if (toolbar) {
                toolbar.classList.add("d-none");
            }
        }, 100);

    },

    _onAIClick(ev) {
        ev.preventDefault();

        const editor = this._getEditor();
        if (!editor) {
            this.notification.add(_t("Editor is not ready yet."), { type: "danger" });
            return;
        }

        // Find the HTML field container
        const div = ev.target.closest("div");
        if (!div) {
            this.notification.add(_t("Could not locate editable field container."), { type: "danger" });
            return;
        }

        // Locate editable content area
        const editable = div.querySelector(".odoo-editor-editable, .note-editable, [contenteditable='true']");
        if (!editable) {
            this.notification.add(_t("Editable content not found."), { type: "danger" });
            return;
        }

        // Automatically select all the content inside editor
        const selection = window.getSelection();
        const range = document.createRange();
        range.selectNodeContents(editable);
        selection.removeAllRanges();
        selection.addRange(range);

        // Extract the text content
        const inputText = editable.innerText.trim();

        // Open proper dialog depending on content presence
        if (inputText) {
            this.openChatGPTDialog(editor, "alternatives", inputText);
        } else {
            this.openChatGPTDialog(editor, "prompt");
        }
    },

});
