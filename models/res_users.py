# -*- coding: utf-8 -*-

import json
from odoo import api, fields, models, _


class ResUsers(models.Model):
    _inherit = "res.users"

    commission_id = fields.Many2one("sale.commission", string="Commission")
    user_commission_line_ids = fields.One2many(
        "user.commission.line", "user_id", string="User Commission"
    )

    def _get_commission_lines(self):
        result = []
        for invoice in self.env["account.move"].search(
            [("invoice_user_id", "=", self.id), ("payment_state", "=", "paid")]
        ):

            date_lis = []
            payment_dict = json.loads(invoice.invoice_payments_widget)
            if payment_dict.get("content"):
                for payment in payment_dict["content"]:
                    date_lis.append(payment["date"])
            last_payment_date = max(date_lis)
            difference = fields.Date.from_string(last_payment_date) - (
                invoice.invoice_date
            )
            diff_days = difference.days

            commission_line = self.commission_id.commission_line_ids.filtered(
                lambda c: c.period_from <= diff_days
                and ((c.period_to >= diff_days) if c.period_to > 0 else True)
            )
            commission_perc = commission_line[0].commission if commission_line else 0.0
            if commission_perc:
                commission_amount = 0.0
                if self.commission_id.based_on == 'amount':
                    commission_amount = (invoice.amount_untaxed * commission_perc) / 100
                else:
                    commission_amount = (invoice.margin * commission_perc) / 100

                result.append(
                    (
                        0,
                        0,
                        {
                            "customer_name":invoice.partner_id.name,
                            "move_id": invoice.id,
                            "move_amount": invoice.amount_untaxed,
                            "move_create_date": invoice.invoice_date,
                            "move_payment_date": fields.Date.from_string(
                                last_payment_date
                            ),
                            "commission_amount": commission_amount,
                            "commission_perc": commission_perc,
                            "payment_interval": int(diff_days),
                            "paid_amount": invoice.amount_total,
                            "tax_amount": invoice.amount_tax,
                            "margin":invoice.margin,
                            "margin_percent":invoice.margin_percent
                        },
                    )
                )
        return result

    def generate_commission_lines(self):
        self.ensure_one()
        if self.commission_id and self.commission_id.commission_line_ids:
            self.user_commission_line_ids.unlink()
            self.user_commission_line_ids = self._get_commission_lines()
        return True


class UserCommissionLine(models.Model):
    _name = "user.commission.line"
    _description = "User Commission Line"

    customer_name = fields.Char('Customer') 
    user_id = fields.Many2one("res.users", "Commission", required=True)
    move_id = fields.Many2one("account.move", "Invoice", required=True)
    move_amount = fields.Float("Untaxed Total Amount")
    move_payment_date = fields.Date("Payment Date")
    move_create_date = fields.Date("Invoice Date")
    commission_amount = fields.Float("Commission Amount")
    commission_perc = fields.Float("Commission(%)")
    payment_interval = fields.Integer("Payment Interval")
    paid_amount = fields.Float("Paid Amount")
    tax_amount = fields.Float("Tax Amount")
    margin = fields.Float("Margin")
    margin_percent = fields.Float("Margin(%)")