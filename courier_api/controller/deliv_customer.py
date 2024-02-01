# -*- coding: utf-8 -*-
import json

from odoo import http, _
from odoo.http import request


class DelivLoginAPI(http.Controller):

    @http.route(['/api/user/signup'], type='json', method="POST",
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
            request.session.authenticate(
                request.session.db, kw.get('login'), kw.get('password'))
            user_id = request.env['res.users'].search(
                [
                    ('login', '=', kw.get('login'))
                ], limit=1).sudo()
            user_id.fbno_user_session = request.session.session_token
            return {
                        'uid': user_id and user_id.id or False,
                        'success': True,
                        'error': None,
                        'profile': user_id.image_1920\
                        if user_id and user_id.image_1920 else False,
                        'session_token': user_id.fbno_user_session
                    }
        except Exception as e:
            return {
                'success': False,
                'error': _('%s' % e)
            }

    @http.route(
        '/api/session/authentication',
        type='json', method="POST", auth="public")
    def session_authenticate(self, **kw):
        user_id = request.env['res.users'].sudo().search([
            ('id', '=', int(kw.get('user_id')))], limit=1).sudo()
        if user_id and kw.get('session_token') and user_id.fbno_user_session\
            and kw.get('session_token') == user_id.fbno_user_session\
            and int(kw.get('user_id')) == user_id.id:
            return {
                'success': True,
                'msg': 'Session Authenticate success'
            }
        return {
                'success': False,
                'msg': 'Session Authenticate Failed'
            }

    @http.route(['/api/user/change_pwd'],
                type='json', method="POST", auth="user")
    def api_user_change_pwd(self, **kw):
        """ User Password Change """
        user = request.env['res.users'].search([
            ("login", "=", kw.get('login'))])
        if not (kw.get('old_password').strip() and kw.get('new_password').strip() and kw.get('confirm_password').strip()):
            return {
                'msg': _('You cannot leave any password empty.'),
                'title':  _('Change Password')}
        if kw.get('new_password') != kw.get('confirm_password'):
            return {
                'msg': _('The new password and its confirmation must be identical.'),
                'title': _('Change Password')
            }
        user.write({'password': kw.get('new_password')})
        return {
            'title': _('Change Password'),
            'msg': _("Password Changed !")
        }

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
        return {
            'shipment_cnt': request.env['courier.courier'].search_count([])}

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
                        'city': city_id.name or '',
                        'area_id': area_id and area_id.id or False,
                        'build_name_id': kw.get('receiverBuildingName'),
                        'flat_id': kw.get('receiverFlat'),
                        'floor_id': kw.get('receiverFloor'),
                    }
                    receiver_id = request.env['res.partner'].create(receiver_vals)
                vals['receiver_id'] = receiver_id and receiver_id.id
            if 'packageType' in kw:
                vals.update({
                    'pickup_delivery_type': 'pickup_and_delivery' if kw['packageType'] == 'Pickup & Delivery' else 'rto' if kw['packageType'] == 'RTO' else 'delivery'
                })
            if 'serviceType' in kw:
                vals.update({
                    'delivery_type': 'express_delivery' if kw['serviceType'] == 'Express Delivery' else 'same_day_delivery' if kw['serviceType'] == 'Same day delivery' else 'normal_delivery'
                })
            if 'sender_id' and 'receiver_id' and 'pickup_delivery_type' and 'delivery_type' in vals:
                courier_id = request.env['courier.courier'].create(vals)
                return {
                    'title': _('Shipment Created'),
                    'msg': _("%s Shipment is Created!") % (courier_id.courier_number),
                    'courier_id': courier_id and courier_id.id
                }

    @http.route([
        '/api/user_edit_profile/<int:user_id>'], type='json', method="POST",
                auth="user")
    def user_edit_profile(self, user_id, **kw):
        """ edit_profile """
        if user_id:
            user_id = request.env['res.users'].search([
                ('id', '=', int(user_id))], limit=1)
            vals = {
                'name': str(kw.get('firstname')) + str(kw.get('lastname')),
                'mobile': kw.get('mobile'),
                }
            if 'email' in kw:
                vals['login'] = kw.get('email')
            user_id.write(vals)
            return {
                'title': _('Profile Record Updated'),
                'msg': _("Profile is Updated!"),
                'status': 'Updated'
            }

    @http.route([
        '/api/manage_contact/create'],
        type='json', method="POST",
        auth="user")
    def manage_contact_create(self, **kw):
        """ Manage Contact Create """
        if kw:
            area_id = request.env['area.area'].search([
                ('name', '=', kw.get('area_name'))], limit=1)
            if not area_id:
                area_id = request.env['area.area'].create({
                    'name': kw.get('area_name'),
                })
            values = {
                'name': kw.get('fullname'),
                'mobile': kw.get('mobile'),
                'city': kw.get('city'),
                'area_id': area_id and area_id.id or False,
                'build_name_id': kw.get('buildingname'),
                'flat_id': kw.get('flat'),
                'floor_id': kw.get('floor'),
            }
            contact_id = request.env['res.partner'].create(values)
            return {
                'title': _('Contact Record Created'),
                'msg': _("Contact is Created!"),
                'status': 'Created',
                'contact_id': contact_id and contact_id.id or False
            }

    @http.route([
        '/api/manage_contact/update/<int:partner_id>'],
        type='json', method="POST",
        auth="user")
    def manage_contact_update(self, partner_id, **kw):
        """ Manage Contact Update """
        if partner_id:
            partner_id = request.env['res.partner'].search([
                ('id', '=', int(partner_id))], limit=1)
            area_id = request.env['area.area'].search([
                ('name', '=', kw.get('addressArea'))], limit=1)
            if not area_id:
                area_id = request.env['area.area'].create({
                    'name': kw.get('addressArea'),
                })
            partner_id.write({'name': kw.get('name'),
                              'mobile': kw.get('mobile'),
                              'email': kw.get('email'),
                              'area_id': area_id and area_id.id or False,
                              'build_name_id': kw.get('addressBuilding'),
                              'flat_id': kw.get('addressFlat'),
                              'floor_id': kw.get('addressFloor'),
                              'gmap_add_id': kw.get('addressGMapAddress')
                              })
            return {
                'title': _('Contact Record Updated'),
                'msg': _("Contact is Updated!"),
                'status': 'Updated'
            }

    @http.route([
        '/api/manage_contact/read/<int:partner_id>'],
        auth='user', type='json', method="POST")
    def manage_contact_read(self, partner_id, **kw):
        """ Manage Contact read """
        if partner_id:
            partner_id = request.env['res.partner'].search([
                ('id', '=', int(partner_id))], limit=1)
            partner_details = {
                'name': partner_id.name,
                'mobile': partner_id.mobile,
                'email': partner_id.email,
                'area_id': partner_id.area_id and partner_id.area_id.id or False,
                'build_name_id': partner_id.build_name_id,
                'flat_id': partner_id.flat_id,
                'floor_id': partner_id.floor_id,
                'gmap_add_id': partner_id.gmap_add_id
            }
            return partner_details

    @http.route([
        '/api/manage_contact/delete/<int:partner_id>'],
        type='json', method="POST",
        auth="user")
    def manage_contact_delete(self, partner_id, **kw):
        """ Manage ontact read """
        if partner_id:
            partner_id = request.env['res.partner'].search([
                ('id', '=', int(partner_id))], limit=1)
            partner_id.unlink()
            return json.dumps({
                'title': _('Contact Record Deleted'),
                'msg': _("Contact is Deleted!"),
                'status': 'Deleted'
            })

    ########################
    @http.route([
        '/api/manage_address/create'],
        type='json', method="POST",
        auth="user")
    def manage_address_create(self, **kw):
        """ Manage Address Create """
        if kw:
            values = {
                'addr_nick_name': kw.get('addr_nick_name'),
                'area_name': kw.get('area_name'),
                'building_name': kw.get('building_name'),
                'floor': kw.get('floor'),
                'flat': kw.get('flat'),
                'landmark': kw.get('landmark'),
                'is_set_primary': kw.get('setprimary')
            }
            address_id = request.env['address.address'].create(values)
            return {
                'title': _('Adress Record Created'),
                'msg': _("Adress is Created!"),
                'status': 'Created',
                'address_id': address_id and address_id.id or False
            }

    @http.route([
        '/api/manage_address/update/<int:address_id>'],
        type='json', method="POST",
        auth="user")
    def manage_address_update(self, address_id, **kw):
        """ Manage Address Update """
        if address_id:
            address_id = request.env['address.address'].search([
                ('id', '=', int(address_id))], limit=1)
            address_id.write({
                             'addr_nick_name': kw.get('addr_nick_name'),
                             'area_name': kw.get('area_name'),
                             'building_name': kw.get('building_name'),
                             'floor': kw.get('floor'),
                             'flat': kw.get('flat'),
                             'landmark': kw.get('landmark'),
                             'is_set_primary': kw.get('setprimary')
                             })
            return {
                'title': _('Address  Updated'),
                'msg': _("Address ated!"),
                'status': 'Updated'
            }

    @http.route([
        '/api/manage_address/read/<int:address_id>'],
        auth='user', type='json', method="POST")
    def manage_address_read(self, address_id, **kw):
        """ Manage Address read """
        if address_id:
            address_id = request.env['address.address'].search([
                ('id', '=', int(address_id))], limit=1)
            address_details = {
                'addr_nick_name': address_id.addr_nick_name,
                'area_name': address_id.area_name,
                'building_name': address_id.building_name,
                'floor': address_id.floor,
                'flat': address_id.flat,
                'landmark': address_id.landmark,
                'is_set_primary': address_id.is_set_primary,
            }
            return address_details

    @http.route([
        '/api/manage_address/delete/<int:address_id>'],
        type='json', method="POST",
        auth="user")
    def manage_address_delete(self, address_id, **kw):
        """ Manage ontact read """
        if address_id:
            address_id = request.env['address.address'].search([
                ('id', '=', int(address_id))], limit=1)
            address_id.unlink()
            return json.dumps({
                'title': _('Address Record Deleted'),
                'msg': _("Address is Deleted!"),
                'status': 'Deleted'
            })
