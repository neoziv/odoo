# -*- coding: utf-8 -*-
# Part of neoziv. See LICENSE file for full copyright and licensing details.

from neoziv.api import Environment
import neoziv.tests

@neoziv.tests.tagged('post_install', '-at_install')
class TestWebsiteHrRecruitmentForm(neoziv.tests.HttpCase):
    def test_tour(self):
        job = self.env['hr.job'].create({
            'name': 'A Test Job',
            'is_published': True,
        })

        self.start_tour("/", 'website_hr_recruitment_tour')

        # check result
        record = self.env['hr.applicant'].search([('description', '=', '### HR RECRUITMENT TEST DATA ###')])
        self.assertEqual(len(record), 1)
        self.assertEqual(record.partner_name, "John Smith")
        self.assertEqual(record.email_from, "john@smith.com")
        self.assertEqual(record.partner_phone, '118.218')
