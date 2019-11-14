#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
import sys
import os
import json
from flask import Flask, jsonify, sendFile, flash, request, redirect, url_for, Response
from werkzeug.utils import secureFilename

app = Flask(__name__)
#sandboxPath = sys.argv[1]
app.config["sandboxPath"] = "alina"
app.config['uploadFolder'] = app.config["sandboxPath"]
allowedExtensions = frozenset(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])


class Sandbox:
    def init(self, path):
        self.path = os.path.realpath(path)

    def isInSandbox(self, path):
        return os.path.commonprefix([self.path, os.path.realpath(path)]) == self.path

class DirectoryTree:
    def init(self, path , maxDepth = 5, sandboxPath = None):
        if sandboxPath:
            self.sandbox = Sandbox(sandboxPath)
            if not self.sandbox.isInSandbox(path):
                raise InvalidUsage('Out of sandbox', statusCode=400)
        else:
            self.sandbox = None
        self.maxDepth = maxDepth
        self.directoryTree = {"back": self.getUpPath(path, 1),
                               "path": os.path.normpath(path),
                               "name": self.getFileName(path),
                               "type": "directory" if self.isDirectory(path) else "file",
                               "size": str(self.getSizeInMegabytes(path)) + " Mb"
                              }
        if self.maxDepth <= 0:
            self.addMetaData("children" , None)
            return
        if self.isDirectory(path):
            self.addMetaData("children", self.scanChildren(path))

    def scanChildren(self, path):
        if self.sandbox:
            return [DirectoryTree(os.path.join(path, ch), self.maxDepth - 1, self.sandbox.path) for ch in os.listdir(path)]
        else:
            return [DirectoryTree(os.path.join(path, ch), self.maxDepth - 1) for ch in os.listdir(path)]

    def getUpPath(self, path, count):
        return os.sep.join(path.split(os.sep)[:-count])

    def addMetaData(self, name, data):
        self.directoryTree[name] = data

    def tStr(self):
        return str(self.directoryTree)

    def getFileName(self, path):
        return os.path.basename(path)

    def isDirectory(self, path):
        return os.path.isdir(path)

    def toJson(self):
        return json.dumps(self, default=lambda o: o.dict["directoryTree"], indent=4)

    def getSizeInMegabytes(self, path):
        return round(os.path.getsize(path)/ 2**10 / 2**10, 2)

class InvalidUsage(Exception):
    statusCode = 400
    def init(self, message, statusCode=None, payload=None):
        Exception.init(self)
        self.message = message
        if statusCode is not None:
            self.statusCode = statusCode
        self.payload = payload

    def toDict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv

@app.errorhandler(InvalidUsage)
def handleInvalidUsage(error):
    response = jsonify(error.toDict())
    response.statusCode = error.statusCode
    return response

class FileManager:
    @staticmethod
    def previewFile(path):
        if not os.path.isfile(path):
            raise InvalidUsage("You cannot preview directory", statusCode=400)
        if os.path.exists(path):
            return sendFile(os.path.abspath(path))
        raise InvalidUsage("File not exist", statusCode=400)


    @staticmethod
    def downloadFile(path):
        if not os.path.isfile(path):
            raise InvalidUsage("You cannot download directory", statusCode=400)
        if os.path.exists(path):
            return sendFile(os.path.abspath(path), asAttachment=True)
        raise InvalidUsage("File not exist", statusCode=400)

    @staticmethod
    def uploadFile(path, file):
        pass #todo

    @staticmethod
    def deleteFile(path):
        if not os.path.exists(path):
            raise InvalidUsage("Not found", statusCode=400)
        os.remove(path)

    @staticmethod
    def createEmptyFile(path, data = ""):
        if not os.path.exists(path):
            with open(path, "w") as f:
                f.write(data)
        else:
            raise InvalidUsage("File already exist", statusCode=400)

    @staticmethod
    def createDir(path):
        if os.path.exists(path):
            raise InvalidUsage("Folder already exists", statusCode=400)
        os.makedirs(path)

    @staticmethod
    def deleteEmptyDir(path):
        if not os.path.exists(path):
            raise InvalidUsage("Not found", statusCode=400)
        os.rmdir(path)


sandbox = Sandbox(app.config["sandboxPath"])
@app.route("/")
def indexfile():
    return """
    <head>
    <style>
    .discription {
        font-style: italic;
        font-size: 12px;
    }
    </style>
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.3.1/jquery.min.js"></script>
    <script src="script.js"></script>
    </head>
    <body>
    </body>"""

@app.route("/script.js")
def hoy():
    with open("script.js") as f:
       return Response(f.read(), mimetype="text/javascript")

@app.route("/getJsonOfDir/<path:subpath>")
def GetJson(subpath):
    if not sandbox.isInSandbox(subpath):
        raise InvalidUsage('Out of sandbox', statusCode=400)
    # return Response(DirectoryTree(subpath,sandboxPath=app.config["sandboxPath"]).toJson(), mimetype="application/json")
    return DirectoryTree(subpath, sandboxPath=app.config["sandboxPath"]).toJson()

@app.route("/createDir/<path:subpath>")
def CreateDir(subpath):
    if not sandbox.isInSandbox(subpath):
        raise InvalidUsage('Out of sandbox', statusCode=400)
    FileManager.createDir(subpath)
    return DirectoryTree(subpath).toJson()

@app.route("/createEmptyFile/<path:subpath>")
def CreateEmptyFile(subpath):
    if not sandbox.isInSandbox(subpath):
        raise InvalidUsage('Out of sandbox', statusCode=400)
    FileManager.createEmptyFile(subpath)
    return DirectoryTree(subpath).toJson()

@app.route("/delete/<path:subpath>")
def Delete(subpath):
    if not sandbox.isInSandbox(subpath):
        raise InvalidUsage('Out of sandbox', statusCode=400)
    if os.path.isfile(subpath) or os.path.islink(subpath):
        FileManager.deleteFile(subpath)
    else:
        FileManager.deleteEmptyDir(subpath)
    return "Success"

@app.route("/downloadFile/<path:subpath>")
def DownloadFile(subpath):
    if not sandbox.isInSandbox(subpath):
        raise InvalidUsage('Out of sandbox', statusCode=400)
    return FileManager.downloadFile(subpath)

@app.route("/previewFile/<path:subpath>")
def PreviewFile(subpath):
    if not sandbox.isInSandbox(subpath):
        raise InvalidUsage('Out of sandbox', statusCode=400)
    return FileManager.previewFile(subpath)

@app.route('/upload/<path:subpath>')
def uploadFile(subpath):
    if not sandbox.isInSandbox(subpath):
        raise InvalidUsage('Out of sandbox', statusCode=400)
    app.config['uploadFolder'] = subpath
    return """<html>
   <body>
      <form action = "http://localhost:8080/uploader" method = "POST"
         enctype = "multipart/form-data">
         <input type = "file" name = "file" />
         <input type = "submit"/>
      </form>
   </body>
</html>"""

@app.route('/uploader', methods = ['GET', 'POST'])
def uploadFilee():
    def allowedFile(filename):
        return '.' in filename and \
    filename.rsplit('.', 1)[1].lower() in allowedExtensions
    if request.method == 'POST':
        f = request.files['file']
        if not allowedFile(f.filename):
            raise InvalidUsage("Bad file name")
        f.save(os.path.join(app.config["uploadFolder"], secureFilename(f.filename)))
        return 'file uploaded successfully'

#StartServer
app.run(debug=True, host="0.0.0.0", port=8080)
