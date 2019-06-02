import os
from pbx_gs_python_utils.utils.Process import Process
from pbx_gs_python_utils.utils.Lambdas_Helpers import slack_message

def log_message(message):
    slack_message(message, [], 'GDL2EC3EE', 'T7F3AUXGV')

def hook(os_path, model, contents_manager):
    git_dir = os.environ.get('CODEBUILD_SRC_DIR')
    if git_dir is None:
        git_dir = '/home/jovyan/work'
    Process.run('git', cwd=git_dir, params=['add', '-A'])
    git_status = Process.run('git', cwd=git_dir, params=['status']).get('stdout')
    Process.run('git', cwd=git_dir, params=['commit', '-m', 'auto saved (changes in notebook)'])
    Process.run('git', cwd=git_dir, params=['pull','--no-edit','origin', 'master'])
    git_result = Process.run('git', cwd=git_dir, params=['push', 'origin','master']).get('stderr')
    if 'rejected' in git_result:
        log_message(':red_circle: on `{0}`, saved to git\n```{1}```\n{2}'.format(os.environ['repo_name'],git_status, git_result))


if False:           # so that we don't get an error in PyCharm
    c=None
#
#  - path: the filesystem path to the file just written - model: the model
#  representing the file - contents_manager: this ContentsManager instance

c.FileContentsManager.post_save_hook = hook

# Configuration file for jupyter-notebook.
