#!/usr/bin/env python
# coding=utf-8

import os
import threading
import model_server
from flask import Flask, request, make_response, render_template as rt
import werkzeug
import shutil
import io
import tarfile

app = Flask(__name__)

class thread_flask_run(threading.Thread):
    def __init__(self, ip, port):
        threading.Thread.__init__(self)
        self.ip = ip
        self.port = port
    def run(self):
        try:
            app.run(self.ip, self.port)
        except Exception as thread_err:
            print ('Upload server thread Error: {}'.format(thread_err) )
            print ('Upload server thread was interupted')
            return 


@app.route('/', methods=['GET', 'POST'])
def index():  # run after one  chunk is uploaded
    if 'dataset_folder' in request.args:
        dataset_folder = request.args.get('dataset_folder')
    save_dir = './jobs/' + dataset_folder # create dir to save file
    if not os.path.exists(save_dir):
    #     shutil.rmtree(save_dir)
        os.mkdir(save_dir)
    return rt('./index.html', dataset_folder = dataset_folder)

@app.route('/upload/<dataset_folder>', methods=['POST'])
def upload(dataset_folder):  # run after one  chunk is uploaded
    
    if request.method == 'POST':
        upload_file = request.files['file']
        task = request.form.get('task_id')  # get file id in upload process
        chunk = request.form.get('chunk', 0)  # get chunk number in all chunks
        filename = '%s%s' % (task, chunk)  # coustruct chunk id

        save_dir = './jobs/' + dataset_folder # create dir to save file
        # raw_input('pause here')
        upload_file.save( save_dir + '/' + filename )  # save chunk in local path

    return rt('./index.html', dataset_folder = dataset_folder)


@app.route('/success/<dataset_folder>', methods=['GET'])
def upload_success(dataset_folder):  # run after all the chunks is upload
    task = request.args.get('task_id')
    ext = request.args.get('ext', '')
    upload_type = request.args.get('type')
    if len(ext) == 0 and upload_type:
        ext = upload_type.split('/')[1]
    ext = '' if len(ext) == 0 else '.%s' % ext  # construct file name
    chunk = 0

    save_dir = './jobs/' + dataset_folder  #  dir to save file
    file_path = save_dir + '/' + dataset_folder + ext #  filename to save file
    
    target_file =  open( file_path, 'w' ) # crate new files
    while True:
        try:
            filename = save_dir + '/' + task + str(chunk)
            source_file = open(filename, 'r')  # open chunks in order
            target_file.write(source_file.read())  # fill the new file with chunks
            source_file.close()
        except IOError:
            break
        chunk += 1
        os.remove(filename)  # delect chunks
    target_file.close()

    extract_dir = save_dir + '/' + 'dataset'
    # dataset_dir = save_dir + '/' + 'dataset'
    if ext == '.zip':
        import zipfile
        """unzip zip file"""
        zip_file = zipfile.ZipFile(file_path)
        if  not os.path.isdir(extract_dir):
            os.mkdir(extract_dir)
        for names in zip_file.namelist():
            zip_file.extract(names, extract_dir)
        zip_file.close()
        # os.rename(extract_dir, dataset_dir)

    if ext == '.rar':
        print 'unrar'
        import rarfile
        """unrar zip file"""
        rar = rarfile.RarFile(file_path)
        if not os.path.isdir(extract_dir):
            os.mkdir(extract_dir)
        os.chdir(extract_dir)
        rar.extractall()
        rar.close()
        # os.rename(extract_dir, dataset_dir)
    return rt('./index.html')

@app.route('/<job_id>/download',
                 methods=['GET', 'POST'],
                 defaults={'extension': 'tar.gz'})
@app.route('/<job_id>/download.<extension>',
                 methods=['GET', 'POST'])
def download(job_id, extension):
    """
    Return a tarball of all files required to run the model
    """
    # job = scheduler.get_job(job_id)

    # if job is None:
    #     raise werkzeug.exceptions.NotFound('Job not found')

    
    iter_num = -1
    # GET ?epoch=n
    print 'job_id---------', job_id
    if 'iter' in request.args:
        iter_num = float(request.args['iter'])
        print 'iter_num-------', iter_num

    job_dir = './jobs/' + job_id
    model_path = job_dir + '/models/model_iter_' + str(iter_num)
    file_path = job_dir + '/' + job_id
    name = 'model_iter_{}'.format(iter_num)
    # if not os.path.exists(job_dir):
        # raise werkzeug.exceptions.BadRequest('Job folder is not existed in server')
    # if not os.path.exists(model_path):
        # raise werkzeug.exceptions.BadRequest('Model folder is not existed in server')
    # Write the stats of the job to json,
    # and store in tempfile (for archive)
    # info = json.dumps(job.json_dict(verbose=False, epoch=epoch), sort_keys=True, indent=4, separators=(',', ': '))
    # info_io = io.BytesIO()
    # info_io.write(info)

    b = io.BytesIO()
    if extension in ['tar', 'tar.gz', 'tgz', 'tar.bz2']:
        # tar file
        mode = ''
        if extension in ['tar.gz', 'tgz']:
            mode = 'gz'
        elif extension in ['tar.bz2']:
            mode = 'bz2'
        with tarfile.open(fileobj=b, mode='w:%s' % mode) as tar:
            # for path, name in job.download_files(epoch):
                    # tar.add(path, arcname=name)
            path = '/home/wills/Projects/digits-ssd/training_server/jobs/ddd/ddd.zip'
            tar.add(path, arcname=name)
            # tar_info = tarfile.TarInfo("info.json")
            # tar_info.size = len(info_io.getvalue())
            # info_io.seek(0)
            # tar.addfile(tar_info, info_io)
    elif extension in ['zip']:
        with zipfile.ZipFile(b, 'w') as zf:
            # for path, name in job.download_files(epoch):
                # zf.write(path, arcname=name)
            path = '/home/wills/Projects/digits-ssd/training_server/jobs/ddd/ddd.zip'
            zf.write(path, arcname=name)
            # zf.writestr("info.json", info_io.getvalue())
    else:
        raise werkzeug.exceptions.BadRequest('Invalid extension')

    response = make_response(b.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=%s_model_iter_%s.%s' % (job_id, iter_num, extension)
    return response


def main():
    pass

if __name__ == '__main__':

    dataset_id = '0.0.0.0'
    dataset_port = 2134
    model_id = '0.0.0.0'
    model_port = 2133

    try:
        flask_run = thread_flask_run(dataset_id, dataset_port)
        flask_run.setDaemon(True)
        flask_run.start()
        model_server.run_training_server(model_id, model_port)
    except KeyboardInterrupt:
        print '\nStop job server'
    #     return
    # mian()