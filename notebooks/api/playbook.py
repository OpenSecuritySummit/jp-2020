from utils import *

class PlaybookToAction():
    def get_target_graph(self, root_issue_id, issues_links_to_copy):
        depth      = 1
        link_types = ','.join(issues_links_to_copy)
        graph      = graph_expand(root_issue_id, depth, link_types)
        return graph

    def apply_text_fixes(self, text):                            # make text transformations
        if text:
            for key,value in self.text_to_replace.items():      # for each value in text_to_replace
                text = text.replace(f'{{{key}}}', value)              # replace variables (that are wrapped using { and } ) 
        return text   

    def create_issue(self, project, issue_type, summary, description):
        summary     = self.apply_text_fixes(summary)                       # apply text fixes
        description = self.apply_text_fixes(description)
        jira_issue  = self.api_jira.issue_create(project, summary, description, issue_type)
        return jira_issue.key

    def add_link(self, from_key, link_type, to_id):
        return self.api_jira.issue_add_link(from_key, link_type, to_id)

    def create_action_issue(self, summary, description):    
        action_id = self.create_issue('ACTION', 'Action', summary, description)
        print(f'Created root ACTION issue "{self.apply_text_fixes(summary)}" with id {action_id}')
        return action_id


    def copy_child_issues(self, root_issue_id, root_issue_data, child_issues, issues_links_to_copy):
    #    issues      = graph.get_nodes_issues(True)                   # get all nodes in graph (more efficient than individual fetch)
        issue_links = root_issue_data.get('Issue Links')              # get all links from the parent issue (the playbook)
        for link_to_copy in issues_links_to_copy:                     # only look for the issues we want to copy
            for linked_issue_id in issue_links.get(link_to_copy,[]):  # issue ids with the link_to_copy link type
                linked_issue = child_issues.get(linked_issue_id)
                issue_type   = linked_issue.get('Issue Type')
                project      = linked_issue.get('Project').upper()
                summary      = linked_issue.get('Summary')
                description  = linked_issue.get('Description')

                new_issue_id = self.create_issue(project, issue_type, summary,description)    # create new child issue
                self.add_link(root_issue_id, link_to_copy, new_issue_id)                      # link it to the root issue
                print(f'Created new {issue_type} "{self.apply_text_fixes(summary)}" and added link "{link_to_copy}" to {root_issue_id}')


    def create_action_from_playbook(self, playbook_key, text_to_replace): 
        self.text_to_replace = text_to_replace
#         self.api_jira        = api_jira_qa_server()                       # use QA server (during development)
        api_jira        = API_Jira()                                 # use live server
        copy_issue_links = ['has task', 'has story','has question']     
        graph            = self.get_target_graph(playbook_key, copy_issue_links)
        playbook_issue   = API_Issues().issue(playbook_key)
        if not playbook_issue:
            raise Exception('TARGET PLAYBOOK DOES NOT EXIST')
        if 'PLAYBOOK' not in playbook_issue['Key']:
            raise Exception('TARGET ISSUE IS NOT A PLAYBOOK')
        action_id        = self.create_action_issue(playbook_issue.get('Summary'), playbook_issue.get('Description'))                    
        self.copy_child_issues(action_id, playbook_issue, graph.get_nodes_issues(True), copy_issue_links)

        return self.api_jira.issue(action_id)


    # todo: add to class and validation
    # # get playbook issue's data
    # playbook_issue = api_issues().issue(playbook_key)

    # if playbook_issue is None or playbook_issue.get('Issue Type') != 'Playbook':
    #     # make sure that none of the cells below work with the wrong id
    #     playbook_key = None                                
    #     # todo: we need a better way to raise this 
    #     raise Exception('target issue is not a Playbook')