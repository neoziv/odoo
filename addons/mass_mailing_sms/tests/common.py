# -*- coding: utf-8 -*-

import re
import werkzeug

from neoziv import tools
from neoziv.addons.mass_mailing.tests.common import MassMailCommon
from neoziv.addons.sms.tests.common import SMSCase, SMSCommon


class MassSMSCase(SMSCase):

    # ------------------------------------------------------------
    # ASSERTS
    # ------------------------------------------------------------

    def assertSMSStatistics(self, recipients_info, mailing, records, check_sms=True):
        """ Deprecated, remove in 14.4 """
        return self.assertSMSTraces(recipients_info, mailing, records, check_sms=check_sms)

    def assertSMSTraces(self, recipients_info, mailing, records,
                        check_sms=True, sent_unlink=False,
                        sms_links_info=None):
        """ Check content of traces. Traces are fetched based on a given mailing
        and records. Their content is compared to recipients_info structure that
        holds expected information. Links content may be checked, notably to
        assert shortening or unsubscribe links. Sms.sms records may optionally
        be checked.

        :param recipients_info: list[{
          # TRACE
          'partner': res.partner record (may be empty),
          'number': number used for notification (may be empty, computed based on partner),
          'state': outgoing / sent / ignored / bounced / exception / opened (outgoing by default),
          'record: linked record,
          # SMS.SMS
          'content': optional: if set, check content of sent SMS;
          'failure_type': error code linked to sms failure (see ``error_code``
            field on ``sms.sms`` model);
          },
          { ... }];
        :param mailing: a mailing.mailing record from which traces have been
          generated;
        :param records: records given to mailing that generated traces. It is
          used notably to find traces using their IDs;
        :param check_sms: if set, check sms.sms records that should be linked to traces;
        :param sent_unlink: it True, sent sms.sms are deleted and we check gateway
          output result instead of actual sms.sms records;
        :param sms_links_info: if given, should follow order of ``recipients_info``
          and give details about links. See ``assertLinkShortenedHtml`` helper for
          more details about content to give;
        ]
        """
        # map trace state to sms state
        state_mapping = {
            'sent': 'sent',
            'outgoing': 'outgoing',
            'exception': 'error',
            'ignored': 'canceled',
            'bounced': 'error',
        }
        traces = self.env['mailing.trace'].search([
            ('mass_mailing_id', 'in', mailing.ids),
            ('res_id', 'in', records.ids)
        ])

        self.assertTrue(all(s.model == records._name for s in traces))
        # self.assertTrue(all(s.utm_campaign_id == mailing.campaign_id for s in traces))
        self.assertEqual(set(s.res_id for s in traces), set(records.ids))

        # check each trace
        if not sms_links_info:
            sms_links_info = [None] * len(recipients_info)
        for recipient_info, link_info, record in zip(recipients_info, sms_links_info, records):
            partner = recipient_info.get('partner', self.env['res.partner'])
            number = recipient_info.get('number')
            state = recipient_info.get('state', 'outgoing')
            content = recipient_info.get('content', None)
            if number is None and partner:
                number = partner._sms_get_recipients_info()[partner.id]['sanitized']

            trace = traces.filtered(
                lambda t: t.sms_number == number and t.state == state and (t.res_id == record.id if record else True)
            )
            self.assertTrue(len(trace) == 1,
                            'SMS: found %s notification for number %s, (state: %s) (1 expected)' % (len(trace), number, state))
            self.assertTrue(bool(trace.sms_sms_id_int))

            if check_sms:
                if state == 'sent':
                    if sent_unlink:
                        self.assertSMSIapSent([number], content=content)
                    else:
                        self.assertSMS(partner, number, 'sent', content=content)
                elif state in state_mapping:
                    sms_state = state_mapping[state]
                    error_code = recipient_info['failure_type'] if state in ('exception', 'ignored', 'bounced') else None
                    self.assertSMS(partner, number, sms_state, error_code=error_code, content=content)
                else:
                    raise NotImplementedError()

            if link_info:
                # shortened links are directly included in sms.sms record as well as
                # in sent sms (not like mails who are post-processed)
                sms_sent = self._find_sms_sent(partner, number)
                sms_sms = self._find_sms_sms(partner, number, state_mapping[state])
                for (url, is_shortened, add_link_params) in link_info:
                    if url == 'unsubscribe':
                        url = '%s/sms/%d/%s' % (mailing.get_base_url(), mailing.id, trace.sms_code)
                    link_params = {'utm_medium': 'SMS', 'utm_source': mailing.name}
                    if add_link_params:
                        link_params.update(**add_link_params)
                    self.assertLinkShortenedText(
                        sms_sms.body,
                        (url, is_shortened),
                        link_params=link_params,
                    )
                    self.assertLinkShortenedText(
                        sms_sent['body'],
                        (url, is_shortened),
                        link_params=link_params,
                    )

    # ------------------------------------------------------------
    # GATEWAY TOOLS
    # ------------------------------------------------------------

    def gateway_sms_click(self, mailing, record):
        """ Simulate a click on a sent SMS. Usage: giving a partner and/or
        a number, find an SMS sent to him, find shortened links in its body
        and call add_click to simulate a click. """
        trace = mailing.mailing_trace_ids.filtered(lambda t: t.model == record._name and t.res_id == record.id)
        sms_sent = self._find_sms_sent(self.env['res.partner'], trace.sms_number)
        self.assertTrue(bool(sms_sent))
        return self.gateway_sms_sent_click(sms_sent)

    def gateway_sms_sent_click(self, sms_sent):
        """ When clicking on a link in a SMS we actually don't have any
        easy information in body, only body. We currently click on all found
        shortened links. """
        for url in re.findall(tools.TEXT_URL_REGEX, sms_sent['body']):
            if '/r/' in url:  # shortened link, like 'http://localhost:8069/r/LBG/s/53'
                parsed_url = werkzeug.urls.url_parse(url)
                path_items = parsed_url.path.split('/')
                code, sms_sms_id = path_items[2], int(path_items[4])
                trace_id = self.env['mailing.trace'].sudo().search([('sms_sms_id_int', '=', sms_sms_id)]).id

                self.env['link.tracker.click'].sudo().add_click(
                    code,
                    ip='100.200.300.400',
                    country_code='BE',
                    mailing_trace_id=trace_id
                )


class MassSMSCommon(MassMailCommon, SMSCommon, MassSMSCase):

    @classmethod
    def setUpClass(cls):
        super(MassSMSCommon, cls).setUpClass()
