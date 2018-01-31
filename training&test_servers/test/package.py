import os
import gzip
import rarfile
import zipfile
import tarfile

def unpack(file_path, extract_dir):
    ext = '.'+file_path.split('.')[-1]
    print 'package file type: ', ext
    if ext == '.zip':
        """unzip zip file"""
        zip_file = zipfile.ZipFile(file_path)
        if  not os.path.isdir(extract_dir):
            os.mkdir(extract_dir)
        for names in zip_file.namelist():
            zip_file.extract(names, extract_dir)
        zip_file.close()
        # os.rename(extract_dir, dataset_dir)

    if ext == '.rar':
        """unrar zip file"""
        rar = rarfile.RarFile(file_path)
        if not os.path.isdir(extract_dir):
            os.mkdir(extract_dir)
        os.chdir(extract_dir)
        rar.extractall()
        rar.close()

    if ext == '.gz':
        """ungz gz file"""
        f_name = file_path.replace(".gz", "")
        g_file = gzip.GzipFile(file_path)
        open(f_name, "w+").write(g_file.read())
        g_file.close()
        """untar tar file"""
        tar = tarfile.open(file_path)
        names = tar.getnames()
        if os.path.isdir(extract_dir):
            pass
        else:
            os.mkdir(extract_dir)
        for name in names:
            tar.extract(name, extract_dir)
        os.remove(f_name)
        tar.close()


    if ext == '.tar':
        """untar tar file"""
        tar = tarfile.open(file_path)
        names = tar.getnames()
        if os.path.isdir(extract_dir):
            pass
        else:
            os.mkdir(extract_dir)
        for name in names:
            tar.extract(name, extract_dir)
        tar.close()

def pack(file_path, extension):
    """
    Return a tarball of all files required to run the model
    """
    package_dir = file_path.split('.')[0] + '.' + extension
    print 'package_dir', package_dir
    name = file_path.split('/')[-1]

    if extension in ['tar', 'tar.gz', 'tgz', 'tar.bz2']:
        # tar file
        mode = ''
        if extension in ['tar.gz', 'tgz']:
            mode = 'gz'
        elif extension in ['tar.bz2']:
            mode = 'bz2'
        with tarfile.open(name=package_dir, mode='w:%s' % mode) as tar:
            tar.add(file_path, arcname=name)
    elif extension in ['zip']:
        with zipfile.ZipFile(b, 'w') as zf:
            zf.write(file_path, arcname=name)
    else:
        pass
        # raise werkzeug.exceptions.BadRequest('Invalid extension')




if __name__ == '__main__':
    file_path = '/home/wills/Projects/digits/training&test_servers/training&test_servers/test/222'
    extract_dir = '/home/wills/Projects/digits/training&test_servers/extract_dir'
    file_path = '/home/wills/Projects/pos.vec'
    pack(file_path, 'tar.gz')