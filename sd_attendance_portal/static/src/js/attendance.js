/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.AttendanceButton = publicWidget.Widget.extend({

    selector: "#attendanceBtn",

    start: function () {
        this.isCheckIn = true;
        this.$btnText = this.$el.find("#btnText");

        this.updateButtonStatus();

        this.$el.on("click", this._onButtonClick.bind(this));

        return this._super.apply(this, arguments);
    },

    // Apply final button colors (guaranteed to work)
    setButtonColor: function () {
        const text = this.$btnText.text();

        if (text === "Check Out") {
            // GREEN BUTTON
            this.$el
                .removeClass("btn-danger")
                .addClass("btn-success")
                .css({
                    "background-color": "#28a745",
                    "border-color": "#28a745",
                    "color": "white",
                });
        } else if (text === "Check In") {
            // RED BUTTON
            this.$el
                .removeClass("btn-success")
                .addClass("btn-danger")
                .css({
                    "background-color": "#dc3545",
                    "border-color": "#dc3545",
                    "color": "white",
                });
        }
    },

    updateButtonStatus: function () {
        var self = this;

        fetch("/portal/get_attendance_status")
            .then((res) => res.json())
            .then((data) => {
                if (data.success && data.message === "Currently checked in") {
                    self.$btnText.text("Check Out");
                    self.isCheckIn = false;
                } else {
                    self.$btnText.text("Check In");
                    self.isCheckIn = true;
                }

                self.setButtonColor(); // Apply correct colors
            })
            .catch((err) => {
                console.error("Error:", err);
                self.$btnText.text("Check In");
                self.isCheckIn = true;

                self.setButtonColor();
            });
    },

    _onButtonClick: function () {
        var self = this;

        const currentTime = new Date().toISOString().slice(0, 19).replace("T", " ");
        const formData = new FormData();

        if (self.isCheckIn) {
            formData.append("check_in", currentTime);
        } else {
            formData.append("check_out", currentTime);
        }

        fetch("/portal/add_attendance", {
            method: "POST",
            body: formData,
        })
            .then((res) => res.json())
            .then((data) => {
                if (data.success) {
                    if (self.isCheckIn) {
                        self.$btnText.text("Check Out");
                    } else {
                        self.$btnText.text("Check In");
                    }

                    self.isCheckIn = !self.isCheckIn;

                    self.setButtonColor();
                } else {
                    alert("Failed: " + data.message);
                }
            })
            .catch((err) => {
                console.error("Error:", err);
                alert("Error while recording attendance.");
            });
    },
});
