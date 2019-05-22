from flask import redirect, url_for, json, request, send_from_directory, _app_ctx_stack
from filesystem import database, api, JWE
from werkzeug.utils import secure_filename
import os
import shutil
import pathlib

d = database

not_allowed = ['exe', 'py', 'sql']

def check_access(id, path):
    cu = database.Users.query.get(id)
    department = path.split("/")[0]
    dep = [x.department for x in cu.departments]
    if cu.userlevel < 5 or department not in dep:
        return True
    else:
        return False

def check_access_view(id, path):
    cu = database.Users.query.get(id)
    department = path.split("/")[0]
    dep = [x.department for x in cu.departments]
    if department not in dep:
        return True
    else:
        return False

from flask_cors import CORS, cross_origin

CORS(app, resources=r'/file/*')

@app.route("/file/uploader/", methods=['GET', 'POST'])
@JWE.requires_auth
def file_uploader():
    data = {"status": "fail"}
    cu = _app_ctx_stack.top.current_user
    if check_access(cu["id"], request.form['path']):
        return json.dumps(data)
    try:
        if request.method == "POST" and "file" in request.files:
            file = request.files['file']
            testFile = os.path.join(config.path + request.form['path'], file.filename)
            if file.filename == "" and file.filename.split(".")[-1] in not_allowed:
                data['message'] = "no name on file"
                pass
            elif os.path.exists(testFile):
                data['message'] = "file already exist!"
                pass
            else:

                filename = secure_filename(file.filename)
                file.save(os.path.join(config.path + request.form['path'], filename))
                data['status'] = "success"
                data['file'] = file.name
        else:
            data['message'] = "no file"
    except Exception as e:
        data['message'] = str(e)
    finally:
        return json.dumps(data)

@app.route("/file/getter/", methods=['GET', 'POST'])
@JWE.requires_auth
def file_viewer():
    data = {"status": "fail"}
    cu = _app_ctx_stack.top.current_user
    if request.method == "GET":
        return send_from_directory(config.path + request.args.get('path'), request.args.get("file"))
    else:
        return "none"


@app.route("/file/remove/<action>/", methods=['GET', 'POST'])
@JWE.requires_auth
def file_remove(action):
    data = {"status": "fail"}
    cu = _app_ctx_stack.top.current_user
    if check_access(cu["id"], request.json['path']):
        return redirect(url_for("logout"))
    data = {"status": "fail"}
    try:
        if action == "file":
            os.remove(os.path.join(config.path + request.json['path'], request.json['file']))
            data['status'] = "success"
        elif action == "directory":
            shutil.rmtree(config.path + request.json['path'])
            data['status'] = "success"
        else:
            data['message'] = "no action"
    except Exception as e:
        data['message'] = str(e)
    finally:
        return json.dumps(data)


#EXPORT MESSAGES
@app.route("/file/export/", methods=["POST", "GET"])
@JWE.requires_auth
def file_export():
    data = {"status": "fail"}
    try:
        if export.write_export_file(request.json['data']):
            data['status'] = "success"
        else:
            data['message'] = "File is Empty"
    except Exception as e:
        data['message'] = str(e)
    finally:
        return json.dumps(data)



@app.route("/file/mri/", methods=['GET', 'POST'])
@JWE.requires_auth
def file_mri():
    data = {"status": "fail"}
    try:
        if request.method == "POST" and "file" in request.files:
            file = request.files['file']
            testFile = os.path.join(config.mri, file.filename)
            mri = d.MRI.query.first()
            if file.filename == "" and file.filename.split(".")[-1] in not_allowed:
                data['message'] = "no name on file"
                pass
            else:
                filename = secure_filename(file.filename)
                file.save(os.path.join(config.mri, filename))
                mri.file = filename
                if "send" in request.form and request.form["send"] == 'true':
                    mri.message = request.form['message']
                    mri.email = True
                else:
                    mri.email = False
                    mri.message = ""
                if config.remote:
                    mriUsers = database.Department.query.filter_by(
                            department="MRI Techs").first()
                    if mri.email and mriUsers and len([x.email for x in mriUsers.allUsers]) != 0:
                        body = """
                                -- UPDATE NOTICE ---
                               """
                        if mri.message != "":
                            body += """
                                    <br/>
                                    <span style="color:red">Message: {}</span> 
                                    <br/>
                                    """.format(mri.message)
                        mymail.send_mail_mri("MRI UPDATE NOTICE",
                                             [x.email for x in
                                              database.Department.query.filter_by(department="MRI Techs").first().allUsers],
                                             body, mri.file
                                             )
                d.db.session.commit()
                data['message'] = mri.message
                data['send'] = mri.email
                data['updateTime'] = mri.lastupdated
                data['status'] = "success"
                data['file'] = filename
        else:
            data['message'] = "no file"
    except Exception as e:
        data['message'] = str(e)
    finally:
        return json.dumps(data)