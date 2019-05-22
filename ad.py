from datetime import datetime, timedelta
from flask import request, json
from filesystem import database, JWE
from ldap3 import Server, Connection, AUTO_BIND_NO_TLS, SUBTREE
import jwe
import datetime

d = database #shorting database name.


def get_ldap_info(u):
    #157
    c = Connection(Server(config.ad_ip, port='0000', use_ssl=False),
                    auto_bind=AUTO_BIND_NO_TLS,
                    read_only=True,
                    check_names=True,
                    user=' ____  ADD ______', password=' ____  ADD ______')
    r = {"bind": c.bind()}
    return r

from flask_cors import CORS, cross_origin
CORS(app, resources=r'/ad/*')

@app.route("/ad/login/", methods=["POST", "GET"])
def login_ad():
    # if request.method == "POST":
    tokendata = {"status": "fail"}
    data = {"status": "fail"}
    try:
        c = Connection(Server(config.ad_ip, port=389, use_ssl=False),
                       auto_bind=AUTO_BIND_NO_TLS,
                       read_only=True,
                       check_names=True,
                       user='firsthealthinc\internal', password='useonly123!')
        if c.bind():
            if "description" in c.result \
                    and c.result['description'] == "success" \
                    and "user" in request.json:

                c.search(search_base='DC=firsthealthinc,DC=com',
                         search_filter='(&(samAccountName={}))'.format(request.json["user"]),
                         search_scope=SUBTREE,
                         attributes=["displayName", "distinguishedName", "memberOf", "sn", "givenName",
                                     "nTSecurityDescriptor",
                                     "msRASSavedFramedIPAddress", "networkAddress", 'title', 'physicalDeliveryOfficeName', 'thumbnailPhoto',
                                     "sAMAccountName", "mail", "mobile",
                                     "telephoneNumber", "department", "company"],
                         paged_size=5)

                # c.search(search_base='DC=firsthealthinc,DC=com', search_filter='(&(CN=*))')
                #
                # result = c.response_to_json()


                if len(json.loads(c.response_to_json())['entries']) > 0 and "password" in request.json:
                    tempV = json.loads(c.response_to_json())
                    c.rebind(user="firsthealthinc\\{}".format(request.json["user"]), password=request.json["password"])
                    if c.result['description'] == "success":
                        data['usercredits'] = c.result
                        user = tempV["entries"][0]
                        data["displayName"] = user["attributes"]["displayName"]
                        data["accountName"] = user["attributes"]["sAMAccountName"]
                        data["mail"] = user["attributes"]["mail"]
                        data['firstname'] = user["attributes"]['givenName']
                        data['lastname'] = user["attributes"]['sn']
                        data["level"] = (user["attributes"]["distinguishedName"]).split(",")[1].split("=")[1]
                        data["memberOf"] = [x.split(",")[0].split("=")[1] for x in (user["attributes"]["memberOf"])]
                        data['company'] = user['attributes']['company'] or ""
                        if user['attributes']['thumbnailPhoto']:
                            data['thumbnailPhoto'] = user['attributes']['thumbnailPhoto']['encoded']
                        else:
                            data['thumbnailPhoto'] = None

                        if user['attributes']['title']:
                            data['title'] = user['attributes']['title']
                        else:
                            data['title'] = None

                        if user['attributes']['physicalDeliveryOfficeName']:
                            data['physicalDeliveryOfficeName'] = user['attributes']['physicalDeliveryOfficeName']
                        else:
                            data['physicalDeliveryOfficeName'] = None


                        if user['attributes']['telephoneNumber']:
                            data['phone'] = user['attributes']['telephoneNumber']
                        else:
                            data['phone'] = None

                        """
                        DATABASE RULES THESE ARE DO TO CHANGE 
                        """

                        u = d.Users.query.filter_by(accountname=data["accountName"]).first()
                        if not u:
                            if data['level'] == "Admins":
                                userlevel = 5
                            else:
                                userlevel = 1
                            if "Domain Admins" in data['memberOf']:
                                userlevel = 9
                            u = d.Users(
                                email=data['mail'],
                                accountname=data['accountName'],
                                userlevel=userlevel,
                                displayname=data['displayName'],
                            )
                            u.firstname = data['firstname']
                            u.lastname = data['lastname']
                            u.organization = data['company']
                            u.phone=data['phone']
                            u.title = data['title']
                            u.thumbnailphoto = data['thumbnailPhoto']
                            u.physicaldeliveryofficename = data['physicalDeliveryOfficeName']
                            d.db.session.add(u)
                            d.db.session.commit()
                            theAll = d.Department.query.filter_by(department="ALL").first()
                            if theAll and theAll not in u.departments:
                                u.departments.append(theAll)

                            for i in data["memberOf"]:
                                dep = d.Department.query.filter_by(department=i).first()
                                if i not in [x.department for x in u.departments] and dep:
                                    u.departments.append(dep)

                            d.db.session.commit()
                        else:
                            u = d.Users.query.filter_by(accountname=data['accountName']).first_or_404()
                            if data['level'] == "Admins":
                                u.userlevel = 5
                            else:
                                u.userlevel = 1
                            if "Domain Admins" in data['memberOf']:
                                u.userlevel = 9

                            u.email = data['mail']
                            u.accountname = data['accountName']
                            u.displayname = data['displayName']
                            u.firstname = data['firstname']
                            u.lastname = data['lastname']
                            u.organization=data['company']
                            u.phone=data['phone']
                            u.title = data['title']
                            u.thumbnailphoto = data['thumbnailPhoto']
                            u.physicaldeliveryofficename = data['physicalDeliveryOfficeName']
                            #dept = d.Department.query.filter(d.Department.department != "ALL").all()

                            d.db.session.commit()
                            count = 0
                            if u.departments:
                                for i in u.departments:
                                    count = count + 1
                                    u.departments.remove(i)

                            d.db.session.commit()

                            u.departments.append(d.Department.query.filter_by(department="ALL").first_or_404())


                            for i in data["memberOf"]:
                                dep = d.Department.query.filter_by(department=i).first()
                                if i not in [x.department for x in u.departments] and dep:
                                    u.departments.append(dep)

                            if u.userlevel == 9:
                                if "MRI Techs" not in [x.department for x in u.departments]:
                                    mri = database.Department.query.filter_by(department="MRI Techs").first()
                                    if mri:
                                        u.departments.append(mri)

                            d.db.session.commit()
                        """
                        END        
                        """

                        """
                        GET USER REST 
                        """
                        u = d.Users.query.get(u.id)
                        ud = [x.id for x in u.departments]
                        data['user'] = d.asdict(u)
                        data['departments'] = [d.asdict(x) for x in d.Department.query.all() if x.id in ud]
                        # if u.userlevel != 9:
                        #     data['messages'] = [x.getDict() for x in d.Message.query.order_by(d.Message.id.desc()).all()
                        #                         if x.department in ud]
                        #     data['departments'] = [d.asdict(x) for x in d.Department.query.all() if x.id in ud]
                        # else:
                        #     data['messages'] = [x.getDict() for x in
                        #                         d.Message.query.order_by(d.Message.id.desc()).all()]
                        #     data['departments'] = [d.asdict(x) for x in d.Department.query.all()]
                        # for i in data['messages']:
                        #     i['user_confirm'] = len(
                        #         d.MessageConfirmed.query.filter_by(user=u.id, message=i['id']).all())
                        data['status'] = "success"
                        tokendata = {}
                        token = {
                            'expires': str(datetime.datetime.now() + timedelta(hours=10)),
                            'userlevel': u.userlevel,
                            'id': u.id,
                            'displayname': u.displayname,
                            'accountname': u.accountname
                        }
                        tokendata['token'] = jwe.encrypt(str.encode(json.dumps(token)), JWE.getEncode()).decode('UTF-8')
                        tokendata['status'] = "success"
                        tokendata['name'] = u.displayname
                        tokendata['userlevel'] = u.userlevel
                    else:
                        data['message'] = "wrong user creds"
                        tokendata['message'] = "wrong user creds"
                else:
                    data["message"] = "wrong password"
                    tokendata['message'] = "wrong password"
            else:
                data['message'] = "wrong user creds"
                tokendata['message'] = "wrong user creds"
        else:
            data["message"] = "can't reach active directory"
            tokendata['message'] = "can't reach active directory"
    except Exception as e:
        data['message'] = str(e)
        tokendata['message'] = str(e)
    finally:
        c.unbind()
        del c
        return json.dumps(tokendata, indent=4, sort_keys=True)


