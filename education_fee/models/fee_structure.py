# -*- coding: utf-8 -*-


from eagle import models, fields, api


class FeeStructure(models.Model):
    _name = 'education.fee.structure'
    _rec_name = 'fee_rate_category'
    fee_structure_name = fields.Char('Name', required=True)
    fee_rate_category=fields.Many2one('education.fee.rate.category',"Fee Rate Category")
    division=fields.Many2one("education.school.division","Division",)
    level=fields.Many2one("education.class","Level")
    group=fields.Many2one("education.division","Group")
    section=fields.Many2one("education.class.division","Section")
    #Todo implement campus shift and Medium Here
    # campus=fields.Many2one()
    start_date=fields.Date("Applicable From")
    end_date=fields.Date("Applicable Till")
    company_currency_id = fields.Many2one('res.currency', compute='get_company_id', readonly=True, related_sudo=False)
    fee_type_ids = fields.One2many('education.fee.structure.lines', 'fee_structure_id', string='Fee Types')
    comment = fields.Text('Additional Information')
    academic_year = fields.Many2one('education.academic.year', string='Academic Year', required=True)
    expire = fields.Boolean('Expire', default=False)
    amount_total = fields.Float('Amount', currency_field='company_currency_id', required=True, compute='compute_total')
    category_id = fields.Many2one('education.fee.category', string='Category', required=True,
                                  default=lambda self: self.env['education.fee.category'].search([], limit=1),
                                  domain=[('fee_structure', '=', True)])

    @api.one
    @api.depends('fee_type_ids.fee_amount')
    def compute_total(self):
        self.amount_total = sum(line.fee_amount for line in self.fee_type_ids)



class FeeStructureLines(models.Model):
    _name = 'education.fee.structure.lines'

    @api.onchange('fee_type')
    def _get_fee_type_ids(self):
        return {
            'domain': {
                'fee_type': [('category_id', '=', self.fee_structure_id.category_id.id)]
            }
        }

    fee_type = fields.Many2one('education.fee.type', string='Fee', required=True)
    fee_structure_id = fields.Many2one('education.fee.structure', string='Fee Structure', ondelete='cascade', index=True)
    fee_amount = fields.Float('Amount',  required=True, related='fee_type.lst_price')
    payment_type = fields.Selection([
        ('onetime', 'One Time'),
        ('permonth', 'Per Month'),
        ('peryear', 'Per Year'),
        ('sixmonth', '6 Months'),
        ('threemonth', '3 Months')
    ], string='Payment Type', related="fee_type.payment_type")
    interval = fields.Char(related="fee_type.interval", string="Interval")
    fee_description = fields.Text('Description', related='fee_type.description_sale')


class FeeType(models.Model):
    _name = 'education.fee.type'
    _inherits = {'product.product': 'product_id'}

    payment_type = fields.Selection([
                                    (0, 'One Time'),
                                    (1, 'Per Month'),
                                    (12, 'Per Year'),
                                    (6, '6 Months'),
                                    (3, '3 Months')
                                ], string='Payment Type', default='permonth',
                                help='Payment type describe how much a payment effective.'
                                     ' Like, bus fee per month is 30 dollar, sports fee per year is 40 dollar, etc')
    interval = fields.Char('Payment Interval', help='Interval describe the payment mode of the fee.'
                                                    'For example, Monthly means the fee must be paid in each month.'
                                                    'Yearly means the payment paid only one time uin year.')

    category_id = fields.Many2one('education.fee.category', string='Category', required=True,
                                  default=lambda self: self.env['education.fee.category'].search([], limit=1))

    @api.model
    def create(self, vals):
        category_id = self.env['education.fee.category'].browse(vals.get('category_id'))
        vals.update({
            'property_account_income_id': category_id.journal_id.default_debit_account_id,
        })
        res = super(FeeType, self).create(vals)
        return res
