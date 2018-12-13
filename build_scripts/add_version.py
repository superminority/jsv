from subprocess import check_output

git_describe = check_output(["git", "describe"]).strip().decode('utf-8')
git_hash = check_output(['git', 'rev-parse', 'HEAD']).strip().decode('utf-8')

ver_parts = git_describe.split('-')
if len(ver_parts == 1):
    release = True
    version = ver_parts[0][1:]
else:
    release = False
