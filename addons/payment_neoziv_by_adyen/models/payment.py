# -*- coding: utf-8 -*-
# Part of neoziv. See LICENSE file for full copyright and licensing details.

import hashlib
import hmac
import json
import logging
from werkzeug import urls

from neoziv import _, api, fields, models
from neoziv.exceptions import ValidationError
from neoziv.addons.payment_neoziv_by_adyen.controllers.main import neozivByAdyenController

_logger = logging.getLogger(__name__)


class AcquirerneozivByAdyen(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[
       ('neoziv_adyen', 'neoziv Payments by Adyen')
    ], ondelete={'neoziv_adyen': 'set default'})
    neoziv_adyen_account_id = fields.Many2one('adyen.account', required_if_provider='neoziv_adyen', related='company_id.adyen_account_id')
    neoziv_adyen_payout_id = fields.Many2one('adyen.payout', required_if_provider='neoziv_adyen', string='Adyen Payout', domain="[('adyen_account_id', '=', neoziv_adyen_account_id)]")

    @api.constrains('provider', 'state')
    def _check_neoziv_adyen_test(self):
        for payment_acquirer in self:
            if payment_acquirer.provider == 'neoziv_adyen' and payment_acquirer.state == 'test':
                raise ValidationError(_('neoziv Payments by Adyen is not available in test mode.'))

    def _get_feature_support(self):
        res = super(AcquirerneozivByAdyen, self)._get_feature_support()
        res['tokenize'].append('neoziv_adyen')
        return res

    @api.model
    def _neoziv_adyen_format_amount(self, amount, currency_id):
        return {
            'value': int(amount * (10 ** currency_id.decimal_places)),
            'currency': currency_id.name,
        }

    @api.model
    def _neoziv_adyen_compute_signature(self, amount, currency_id, reference):
        secret = self.env['ir.config_parameter'].sudo().get_param('database.secret')
        token_str = '%s%s%s' % (
            int(amount * (10 ** currency_id.decimal_places)),
            currency_id.name,
            reference
        )
        return hmac.new(secret.encode('utf-8'), token_str.encode('utf-8'), hashlib.sha256).hexdigest()

    def neoziv_adyen_form_generate_values(self, values):
        # Don't use the value returned by `self.get_base_url` for the notification_url as
        # `request.httprequest.url_root` could be forged to retrieve the signature and
        # fake a payment update
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        data = {
            'adyen_uuid': self.neoziv_adyen_account_id.adyen_uuid,
            'payout': self.neoziv_adyen_payout_id.code,
            'amount': self._neoziv_adyen_format_amount(values['amount'], values['currency']),
            'reference': values['reference'],
            'shopperLocale': values.get('partner_lang'),
            'metadata': {
                'merchant_signature': self._neoziv_adyen_compute_signature(values['amount'],values['currency'],values['reference']),
                'notification_url': urls.url_join(base_url, neozivByAdyenController._notification_url),
            },
            'returnUrl': urls.url_join(self.get_base_url(), '/payment/process'),
        }

        if self.save_token in ['ask', 'always']:
            data.update({
                'shopperReference': '%s_%s' % (self.neoziv_adyen_account_id.adyen_uuid, values['partner_id']),
                'storePaymentMethod': True,
                'recurringProcessingModel': 'CardOnFile',
            })

        values.update({
            'data': json.dumps(data),
        })
        return values

    def neoziv_adyen_get_form_action_url(self):
        self.ensure_one()
        proxy_url = self.env['ir.config_parameter'].sudo().get_param('adyen_platforms.proxy_url')
        return urls.url_join(proxy_url, 'pay_by_link')

    def neoziv_adyen_create_account(self):
        return self.env['adyen.account'].action_create_redirect()

class TxneozivByAdyen(models.Model):
    _inherit = 'payment.transaction'

    def neoziv_adyen_s2s_do_transaction(self, **kwargs):
        self.ensure_one()
        # Don't use the value returned by `self.get_base_url` for the notification_url as
        # `request.httprequest.url_root` could be forged to retrieve the signature and
        # fake a payment update
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        data = {
            'payout': self.acquirer_id.neoziv_adyen_payout_id.code,
            'amount': self.acquirer_id._neoziv_adyen_format_amount(self.amount, self.currency_id),
            'reference': self.reference,
            'paymentMethod': {
                'type': self.payment_token_id.neoziv_adyen_payment_method_type,
                'storedPaymentMethodId': self.payment_token_id.acquirer_ref,
            },
            'shopperReference': '%s_%s' % (self.acquirer_id.neoziv_adyen_account_id.adyen_uuid, self.partner_id.id),
            'shopperInteraction': 'ContAuth',
            'metadata': {
                'merchant_signature': self.acquirer_id._neoziv_adyen_compute_signature(self.amount, self.currency_id, self.reference),
                'notification_url': urls.url_join(base_url, neozivByAdyenController._notification_url),
            },
            'returnUrl': urls.url_join(self.get_base_url(), '/payment/process'),
        }
        self.acquirer_id.neoziv_adyen_account_id._adyen_rpc('payments', data)

    @api.model
    def _neoziv_adyen_form_get_tx_from_data(self, data):
        reference = data.get('merchantReference')
        if not reference:
            error_msg = _('neoziv Payments by Adyen: received data with missing reference (%s)', reference)
            _logger.info(error_msg)
            raise ValidationError(error_msg)

        tx = self.env['payment.transaction'].search([('reference', '=', reference)])
        if not tx or len(tx) > 1:
            error_msg = _('neoziv Payments by Adyen: received data for reference %s') % (reference)
            if not tx:
                error_msg += _('; no order found')
            else:
                error_msg += _('; multiple order found')
            _logger.info(error_msg)
            raise ValidationError(error_msg)

        return tx

    def _neoziv_adyen_form_get_invalid_parameters(self, data):
        invalid_parameters = []

        if self.acquirer_reference and data.get('pspReference') != self.acquirer_reference:
            invalid_parameters.append(('pspReference', data.get('pspReference'), self.acquirer_reference))

        return invalid_parameters

    def _neoziv_adyen_form_validate(self, data):
        merchant_signature = self.acquirer_id._neoziv_adyen_compute_signature(self.amount, self.currency_id, self.reference)
        if merchant_signature != data['additionalData']['metadata.merchant_signature']:
            return False

        # Save token
        if self.partner_id and not self.payment_token_id and \
               (self.type == 'form_save' or self.acquirer_id.save_token == 'always') \
               and 'recurring.shopperReference' in data['additionalData']:
            res = self.acquirer_id.neoziv_adyen_account_id._adyen_rpc('payment_methods', {
                'shopperReference': data['additionalData']['recurring.shopperReference']
            })
            stored_payment_methods = res['storedPaymentMethods']
            pm_id = data['additionalData']['recurring.recurringDetailReference']
            token_id = self.env['payment.token'].create({
                'name': _("Card No XXXXXXXXXXXX%s", data['additionalData']['cardSummary']),
                'acquirer_ref': pm_id,
                'acquirer_id': self.acquirer_id.id,
                'partner_id': self.partner_id.id,
                'neoziv_adyen_payment_method_type': next(pm['type'] for pm in stored_payment_methods if pm['id'] == pm_id)
            })
            self.payment_token_id = token_id

        # Update status
        if data['success']:
            self.write({'acquirer_reference': data.get('pspReference')})
            self._set_transaction_done()
            return True
        else:
            error = _('neoziv Payment by Adyen: feedback error')
            _logger.info(error)
            self.write({'state_message': error})
            self._set_transaction_cancel()
            return False

class PaymentToken(models.Model):
    _inherit = 'payment.token'

    neoziv_adyen_payment_method_type = fields.Char(string='PaymentMethod Type')
