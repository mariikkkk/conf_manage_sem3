@echo off
setlocal
cd /d %~dp0\..
python -c "import zipfile,io; b=io.BytesIO(); z=zipfile.ZipFile(b,'w',zipfile.ZIP_DEFLATED); z.writestr('a.txt','A\n'); z.writestr('b.txt','B\n'); z.writestr('img/',''); z.close(); open('vfs_multi.zip','wb').write(b.getvalue())"
echo created vfs_multi.zip
python main.py --vfs vfs_multi.zip
