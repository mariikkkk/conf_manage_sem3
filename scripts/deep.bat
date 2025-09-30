@echo off
setlocal
cd /d %~dp0\..
python -c "import zipfile,io; b=io.BytesIO(); z=zipfile.ZipFile(b,'w',zipfile.ZIP_DEFLATED); z.writestr('lvl1/lvl2/lvl3/readme.txt','deep\n'); z.writestr('lvl1/lvl2/empty/',''); z.close(); open('vfs_deep.zip','wb').write(b.getvalue())"
echo created vfs_deep.zip
python main.py --vfs vfs_deep.zip
