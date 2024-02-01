# -*- coding: utf-8 -*-
import base64
import json


from odoo import http, _
from odoo.http import request
from odoo.exceptions import AccessError, UserError


class DelivLoginAPI(http.Controller):

    @http.route(
        [
            '/api/user/signup'
        ], type='json', method="POST",
                auth="public")
    def api_user_signup(self, **kw):
        """Signup API : Take the user input with login/name/password (As mandayory)
        """
        user_obj = request.env["res.users"].sudo()
        user = user_obj.search([("login", "=", kw.get('login'))])
        if not user:
            user = request.env['res.users'].sudo().search([
                ('login', '=', kw.get('login'))], limit=1)
        if not user:
            values = {'login': kw.get('login'),
                      'name': kw.get('name') or kw.get('login'),
                      'password': kw.get('password'),
                      'mobile': kw.get('mobile')}
            db, login, password = request.env['res.users'].sudo().signup(values)
            if not login:
                return {
                    'success': False,
                    'error': _('Could not create a new account.'),
                    'msg': _("Unknown error while creating an account.")
                }
            user = user_obj.search([("login", "=", login)])
        return {'success': True, 'error': None}

    @http.route(['/api/user/login'],
                type='json', method="POST", auth="public")
    def api_user_login(self, **kw):
        ''' Login API : authenticate the user credential.'''
        try:
            request.session.authenticate(request.session.db, kw.get('login'), kw.get('password'))
            return {'success': True, 'error': None}
        except Exception as e:
            return {
                'success': False,
                'error': _('%s' % e)
            }

    @http.route(['/api/user/change_pwd'],
                type='http', method="POST", auth="user", csrf=False)
    def api_user_change_pwd(self, **kw):
        """ User Password Change """
        user = request.env['res.users'].search([
            ("login", "=", kw.get('login'))])
        if not (kw.get('old_password').strip() and kw.get('new_password').strip() and kw.get('confirm_password').strip()):
            return json.dumps({
                'msg': _('You cannot leave any password empty.'),
                'title':  _('Change Password')})
        if kw.get('new_password') != kw.get('confirm_password'):
            return json.dumps({
                'msg': _('The new password and its confirmation must be identical.'),
                'title': _('Change Password')
            })
        user.write({'password': kw.get('new_password')})
        return json.dumps({
            'title': _('Change Password'),
            'msg': _("Password Changed !")
        })

    @http.route(
        ['/api/get/user_details/<int:user_id>'],
        auth='user', type='json', method="POST")
    def get_user_details(self, user_id, **kw):
        """ Get the User Specific Infrormation"""
        if user_id:
            user = request.env["res.users"].search([
                ("id", "=", int(user_id))], limit=1)
            user_details = {
                "name": user.name,
                "email": user.email,
                'state': user.state
            }
            return user_details

    @http.route(
        ['/api/get/shipment_count'],
        auth='user', type='json', method="POST")
    def get_shipment_count(self, **kw):
        """ Get the Shipment Counter"""
        return {'shipment_cnt': request.env['courier.courier'].search_count([])}

    @http.route(
        ['/api/get/shipment/detail'],
        auth='user', type='json', method="POST")
    def get_shipment_detail(self, **kw):
        """ Get the Shipment Detail"""
        courier_details = [
            {
                'courier_number': courier.courier_number,
                'delivery_type': courier.delivery_type,
                'sender_id': courier.sender_id,
                'receiver_id': courier.receiver_id
            } for courier in request.env['courier.courier'].search([])]
        return courier_details

    @http.route('/api/create_shipment_api', type='json', method="POST",
                auth="user")
    def create_shipment(self, **kw):
        """ Create Shipment API"""
        vals = {}
        if kw:
            if 'senderName' in kw:
                sender_id = request.env['res.partner'].search([
                    ('name', '=', kw.get('senderName'))], limit=1)
                area_id = request.env['area.area'].search([
                    ('name', '=', kw.get('senderArea'))], limit=1)
                city_id = request.env['city.city'].search([
                    ('name', '=', kw.get('senderCity'))], limit=1)
                if 'senderArea' in kw:
                    if not city_id:
                        city_id = request.env['city.city'].create({
                            'name': kw.get('senderCity'),
                        })
                    if not area_id:
                        area_id = request.env['area.area'].create({
                            'name': kw.get('senderArea'),
                            'city_id': city_id and city_id.id or False
                        })
                if not sender_id:
                    sender_vals = {
                        'name': kw.get('senderName'),
                        'mobile': kw.get('senderMobileNumber'),
                        'email': kw.get('senderEmail'),
                        'city': city_id.name or '',
                        'area_id': area_id and area_id.id or False,
                        'build_name_id': kw.get('senderBuildingName'),
                        'flat_id': kw.get('senderFlat'),
                        'floor_id': kw.get('senderFloor'),
                    }
                    sender_id = request.env['res.partner'].create(sender_vals)
                vals['sender_id'] = sender_id and sender_id.id
            if 'receiverName' in kw:
                receiver_id = request.env['res.partner'].search([
                    ('name', '=', kw.get('receiverName'))], limit=1)
                area_id = request.env['area.area'].search([
                    ('name', '=', kw.get('receiverArea'))], limit=1)
                city_id = request.env['city.city'].search([
                    ('name', '=', kw.get('receiverCity'))], limit=1)
                if 'receiverArea' in kw:
                    if not city_id:
                        city_id = request.env['city.city'].create({
                            'name': kw.get('receiverCity'),
                        })
                    if not area_id:
                        area_id = request.env['area.area'].create({
                            'name': kw.get('receiverArea'),
                            'city_id': city_id and city_id.id or False
                        })
                if not receiver_id:
                    receiver_vals = {
                        'name': kw.get('receiverName'),
                        'mobile': kw.get('receiverMobileNumber'),
                        'email': kw.get('receiverEmail'),
                        'city': city_id.name or '',
                        'area_id': area_id and area_id.id or False,
                        'build_name_id': kw.get('receiverBuildingName'),
                        'flat_id': kw.get('receiverFlat'),
                        'floor_id': kw.get('receiverFloor'),
                    }
                    receiver_id = request.env['res.partner'].create(receiver_vals)
                vals['receiver_id'] = receiver_id and receiver_id.id
            if 'is_cod' in kw:
                vals['cod'] = kw.get('is_cod')
            if 'cod' in vals and vals['cod']:
                vals['cod_amount'] = kw.get('cod_amount')

            pkg_vals =[]
            courier_details = kw.get("package_details")
            for rec in courier_details:
                pkg_vals.append((0, 0, {
                    'product_description': rec.get('description_note'),
                    'product_packaging_id': rec.get('package_type'),
                    'no_of_boxes': rec.get('no_of_packages'),
                }))
            vals.update({
                'fbno_tree_id': pkg_vals,
                })
            if 'packageType' in kw:
                vals.update({
                    'pickup_delivery_type': 'pickup_and_delivery' if kw[
                                                                         'packageType'] == 'Pickup & Delivery' else 'rto' if
                    kw['packageType'] == 'RTO' else 'delivery'
                })
            if 'serviceType' in kw:
                vals.update({
                    'delivery_type': 'express_delivery' if kw[
                                                               'serviceType'] == 'Express Delivery' else 'same_day_delivery' if
                    kw['serviceType'] == 'Same day delivery' else 'normal_delivery'
                })
            if 'sender_id' and 'receiver_id' and 'pickup_delivery_type' and 'delivery_type' in vals:
                courier_id = request.env['courier.courier'].create(vals)
                return {
                    'title': _('Shipment Created'),
                    'msg': _("%s Shipment is Created!") % (courier_id.courier_number),
                    'courier_id': courier_id and courier_id.id
                }
    @http.route('/api/cancel_shipment_api', type='http', method="POST",
                auth="user", csrf=False)
    def cancel_shipment(self, **kw):
        """ Cancel Shipment """
        if kw and 'shipment_id' in kw:
            courier_id = request.env['courier.courier'].search([
                ('id', '=', int(kw.get('shipment_id')))], limit=1)
            courier_number = courier_id.courier_number
            courier_id.cancel_courier_express()
            return json.dumps({
                'title': _('Shipment Cancel'),
                'msg': _("%s Shipment is Cancel!") % (courier_number),
                'status': 'Cancel'
            })

    @http.route([
        '/api/update_shipment_api/<int:user_id>'], type='http', method="POST",
                auth="user", csrf=False)
    def update_shipment(self, user_id, **kw):
        """ Update Shipment """
        if user_id:
            user_id = request.env['res.users'].search([
                ('id', '=', int(user_id))], limit=1)
            user_id.write({
                'name': kw.get('firstname'), 'mobile': kw.get('mobile')})
            return json.dumps({
                'title': _('Shipment Record Updated'),
                'msg': _("Shipment is Updated!"),
                'status': 'Updated'
            })

    @http.route([
        '/api/dashboard_count/<int:user_id>'],
        type='json', method="get", auth="user")
    def dashboard_count(self, user_id, **kw):
        """ dashboard_count """
        if user_id:
            return {
                'completed_trips': request.env['courier.courier'].search_count([('assign_driver', '=', int(user_id)), ('state', 'in', ['delivered', 'inscan'])]),
                'total_trips': request.env['courier.courier'].search_count([('assign_driver', '=', int(user_id))]),
                'pending_trips': request.env['courier.courier'].search_count([('assign_driver', '=', int(user_id)), ('state', 'in', ['outscan', 'out_for_delivery'])]),
                'cancel_trips': request.env['courier.courier'].search_count([('assign_driver', '=', int(user_id)), ('state', '=',  'cancel')]),
                'today_total_trips': request.env['courier.courier'].search_count([('assign_driver', '=', int(user_id)), ('fbno_assign_driver_date', '=', fields.Date.today())]),
                'today_completed_trips': request.env['courier.courier'].search_count([('assign_driver', '=', int(user_id)), ('state', 'in', ['delivered', 'inscan']), ('fbno_assign_driver_date', '=', fields.Date.today())]),
                'today_pending_trips': request.env['courier.courier'].search_count([('assign_driver', '=', int(user_id)), ('state', 'in', ['outscan', 'out_for_delivery']), ('fbno_assign_driver_date', '=', fields.Date.today())]),
                'today_cancel_trips': request.env['courier.courier'].search_count([('assign_driver', '=', int(user_id)), ('state', '=',  'cancel'), ('fbno_assign_driver_date', '=', fields.Date.today())]),
                'cost_of_day': sum(request.env['courier.courier'].search([('assign_driver', '=', int(user_id)), ('fbno_assign_driver_date', '=', fields.Date.today())]).mapped('fbno_delivery_total'))
            }

    @http.route([
        '/api/runsheet_detail/<int:user_id>'],
        type='json', method="get", auth="user")
    def runsheet_detail(self, user_id, **kw):
        """ runsheet details API """
        if user_id:
            courier_ids = request.env['courier.courier'].search(
                [
                    ('assign_driver', '=', int(user_id))
                ]
            )
            courier_list = [{
                    'courier_number': courier_id.courier_number,
                    'sender_id': courier_id.sender_id and courier_id.sender_id.id or False,
                    'receiver_id': courier_id.receiver_id and courier_id.receiver_id.id or False,
                    'pickup_time': courier_id.pickup_time,
                    'packg_size': courier_id.packg_size,
                    'cod_amount': courier_id.cod_amount,
                    'receiver_id_phone': courier_id.receiver_id.phone,
                    'receiver_id_mobile': courier_id.receiver_id.mobile,
                } for courier_id in courier_ids]
            return courier_list

    @http.route(
        ['/api/get/collection_shipmemt/<int:courier_id>'],
        auth='user', type='json', method="POST")
    def get_collection_shipmemt(self, courier_id, **kw):
        """ Get the Collection Shipmemt Specific Infrormation"""
        if courier_id:
            courier_id = request.env["courier.courier"].search([
                ("id", "=", int(courier_id)),
                ('pickup_delivery_type', '=', 'pickup_and_delivery')], limit=1)
            courier_state = courier_id.state_express if courier_id.delivery_type == 'express_delivery' else courier_id.state
            collection_ship_detail = {
                "status": courier_state,
                "delivery_type": courier_id.delivery_type,
                "Area": courier_id.receiver_id.area_id.name,
                "area_id": courier_id.receiver_id.area_id and courier_id.receiver_id.area_id.id or False,
            }
            return collection_ship_detail

    @http.route(
        ['/api/get/delivery_status/<int:courier_id>'],
        auth='user', type='json', method="POST")
    def get_non_delivery_status(self, courier_id, **kw):
        """ Get the hipmemt Specific Infrormation Status"""
        if courier_id:
            courier_id = request.env["courier.courier"].search([
                ("id", "=", int(courier_id))], limit=1)
            courier_state = courier_id.state_express if courier_id.delivery_type == 'express_delivery' else courier_id.state
            ship_detail = {
                "status": courier_state
            }
            return ship_detail

    @http.route([
        '/api/runsheet_scan_barcode/<int:user_id>'],
        type='json', method="POST", auth="user")
    def runsheet_scan_barcode(self, user_id, **kw):
        """ runsheet scan barcode API """
        if user_id:
            courier_id = request.env['courier.courier'].search(
                [
                    ('assign_driver', '=', int(user_id)),
                    ('courier_number', '=', kw.get('courier_number'))
                ], limit=1
            )
            courier_id.state_express = 'delivered'
            return {
                'title': _('Shipment Updated'),
                'msg': _("Runsheet Scan Courier - %s is Delivered!") % (courier_id.courier_number),
                'status': 'Delivered'
            }

    @http.route(
        ['/api/proof_of_delivery/<int:courier_id>'],
        auth='user', type='json', method="POST")
    def proof_of_delivery(self, courier_id, **kw):
        """ Proof Of Delivery"""
        if courier_id and 'filename' in kw:
            courier_id = request.env["courier.courier"].search([
                ("id", "=", int(courier_id))], limit=1)
            try:
                for k, v in kw.items():
                    courier_id.write({
                        'packg_img': base64.encodebytes(v.stream.read())})
                return {'status': 'success', 'courier_id': courier_id.ifd}
            except:
                return {'status': 'error', 'status_code': 500}
