from odoo import fields, models, api
import uuid
import random
import string
from odoo.exceptions import ValidationError

class IdApplication(models.Model):
    _name = 'id.application'
    _description = 'National Id Application'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    name = fields.Char('Applicant Full name', required=True)
    date_of_birth = fields.Date('Date of Birth', required=True)
    sex = fields.Selection([
            ('male', 'Male'),
            ('female', 'Female')
        ])
    country_of_origin = fields.Char('Country of Origin', required=True)
    parent_nin = fields.Char('Parent NIN')


    lc_letter = fields.Binary('LC Reference Letter', required=True)
    photo = fields.Binary('Applicant Photo', required=True)
    nin = fields.Char('National ID Number', readonly=True, copy=False, default='New')
    stage = fields.Selection([
            ('draft', 'Draft'),
            ('submitted', 'Submitted'),
            ('approved_stage1', 'Approved Stage 1'),
            ('approved_stage2', 'Approved Stage 2'),
            ('rejected', 'Rejected'),
        ], default='draft', string='Status')


    def _generate_nin(self):
        '''
            Method to generate unique ID number
        '''
        uid = self.env['ir.sequence'].next_by_code('id.application')
        print('---------------------',uid)
        return uid

    @api.model
    def create(self, vals):
        ''' Override the create method to automatically generate National ID'''
        if vals.get('nin', 'New') == 'New':
            sequence = self._generate_nin()
            print("**********************", sequence)
            random_alpha = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            vals['nin'] = f'{sequence}{random_alpha}'

        return super(IdApplication, self).create(vals)

    @api.constrains('date_of_birth')
    def _check_age(self):
        ''' Ensure the applicants are over 16 years'''
        for record in self:
            if record.date_of_birth:
                today = fields.Date.today()
                age = today.year - record.date_of_birth.year
                if age < 16:
                    raise ValidationError('Applicant must be at least 16 years')



    def submit_application(self):
        self.stage = 'submitted'
        self.message_post(body='Application submitted by %s' % self.env.user.name)


    def approve_stage1(self):
        if self.stage != 'submitted':
            raise ValidationError('Cannot approve applications that have not been submitted')
        self.stage = 'approved_stage1'
        self.message_post(body='Approved at Stage 1 by %s' % self.env.user.name)


    def approve_stage2(self):
        if self.stage != 'approved_stage1':
            raise ValidationError('Cannot approve applications that have not passed stage 1 approval')
        self.stage = 'approved_stage2'
        self.message_post(body='Approved at Stage 2 by %s' % self.env.user.name)


    def reject_application(self):
        self.stage = 'rejected'
        self.message_post(body='Application rejected by %s' % self.env.user.name)
