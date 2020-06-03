### THIS NEEDS TO BE ADDED TO THE MAIN OSBOT_JUPITER project so that it is available to all notebooks
import json
import qgrid
import pandas as pd
from jira                                     import JIRA
from time                                     import sleep
from IPython.display                          import display_html
from IPython.core.display                     import HTML
from pbx_gs_python_utils.utils.Process        import Process
from osbot_jupyter.api_notebook.Jp_Graph_Data import Jp_Graph_Data
from osbot_jupyter.api_notebook.Jp_Jira       import Jp_Jira
from osbot_jira.api.graph.Lambda_Graph        import Lambda_Graph
from osbot_jira.api.graph.Graph_View          import Graph_View
from osbot_jira.api.graph.GS_Graph            import GS_Graph
from osbot_jira.api.jira_server.API_Jira      import API_Jira
from osbot_jira.api.jira_server.API_Jira_Rest import API_Jira_Rest
from osbot_jira.api.API_Issues                import API_Issues
from osbot_jira.Jira                          import Jira
from osbot_jupyter.api_notebook.Edit_UI       import Edit_UI
from osbot_aws.apis.Lambda                    import Lambda

#jira = Jira()

# API helpers

def api_issues():
    return API_Issues()

def elastic():
    return api_issues().elastic()

def api_jira():
    return API_Jira()

def api_jira_qa_server():
    api_jira    = API_Jira()
    api_jira.secrets_id = 'GS_BOT_GS_JIRA_QA'
    return api_jira

# MISC Utils

def list_notebooks():
    return Process.run('find', ["-type", "f", "-name", "*.ipynb"], cwd='../../..').get('stdout').split('\n')


def find_notebook(name):
    name = name.lower()
    for file in list_notebooks():
        if name in file.lower():
            return file


def find_notebooks(name):
    results = []
    name = name.lower()
    for file in list_notebooks():
        if name in file.lower():
            results.append(file)
    return results


def send_png_to_slack(png_data, channel, team_id):
    Lambda('gw_bot.lambdas.png_to_slack').invoke({'png_data': png_data, 'team_id': team_id, 'channel': channel})


# edit UI
    #issue_id = 'Task-40'
def edit_issue(issue_id):
    return Edit_UI(issue_id).show_ui()

# pandas

def graph_table(graph, columns=None):
    if columns is None:
        columns = ['Key', 'Summary', 'Status', 'Assignee', 'Issue Links', 'Issue Type', 'Labels', 'Latest Information',
                   'Priority', 'Project', 'Rating']  # , 'Description']
    return pd.DataFrame(graph.get_nodes_issues(reload=True).values(), columns=columns).set_index('Key')


#    return pd.DataFrame(graph.get_nodes_issues(reload=True))

def graph_grid(graph):
    display_html(qgrid.show_grid(graph_table(graph)))


def graph_render(graph, height=200):
    puml = graph.render_puml().puml
    puml_render(puml, height)

def puml_render(puml, height=200):
    png_data = Lambda('gw_bot.lambdas.puml_to_png').invoke({"puml": puml}).get('png_base64')
    show_png(png_data,height)


def show_graph(graph_name, height=500):
    print('creating plantuml graph for: {0}'.format(graph_name))

    png_data = Lambda_Graph().get_graph_png___by_name(graph_name).get('png_base64')
    show_png(png_data, height)


def show_png(png_data, height=200):
    html = '<img style="border:1px solid black;height:{0}pt;" align="left" src="data:image/png;base64,{1}"/>'.format(
        height, png_data)
    display_html(html, raw=True)


def search(query, show_img=False, height=200):
    params = ['Issue\ Type:Role']
    jp_graph = Jp_Graph_Data()
    api_issues = jp_graph.api_issues
    elk_to_slack = jp_graph.elk_to_slack
    api_issues.elastic().set_index(api_issues.index)  # BUG: this should happen automatically
    issues = api_issues.search_using_lucene(query)
    graph_name = elk_to_slack.save_issues_as_new_graph(issues)
    print("Created graph '{0}' with search for '{1}' with '{2}' matches".format(graph_name, query, len(issues)))

    if show_img:
        sleep(1)
        show_graph(graph_name, height)
    return issues


def project_schema(project_name):
    jp_graph     = Jp_Graph_Data()
    api_issues   = jp_graph.api_issues
    elk_to_slack = jp_graph.elk_to_slack
    issues       = api_issues.search_using_lucene(f'Project:{project_name.upper()}')
    graph_name   = elk_to_slack.save_issues_as_new_graph(issues)
    Lambda_Graph().wait_for_elk_to_index_graph(graph_name)
    graph        = jp_graph.jira_links(graph_name)
    display(HTML(f"<h2>{project_name}</h2>"))
    render_puml(Graph_View(graph).view_schema())    
    
# methods to move to main APIs


def jira_links(source, depth=1, show=True):
    graph_data = Jp_Graph_Data()
    graph      = graph_data.jira_links(source, depth)
    if show:
        render_puml(graph.render_puml().puml)
    return graph

def graph_expand(source, depth, link_types, height=200, show=True):
    jp_graph = Jp_Graph_Data()
    graph = jp_graph.graph_expand(source, depth, link_types)
    graph_name = graph.reset_puml().render_and_save_to_elk()
    if show:
        sleep(1);      # give time for the graph to be saved (needs better solution)
        show_graph(graph_name, height)
    return graph

    
def epic_graph(key):
    return GS_Graph().add_nodes_from_epics()


#     graph = GS_Graph()
#     (graph.set_links_path_mode_to_down()
#           .add_all_linked_issues([key], 1)
#           .add_nodes_from_epics()
#           .add_all_linked_issues()
#      )
#     return graph


# show/render issues

def show_issue(issue_id):
    Jp_Jira().issue(issue_id)


def show_issues(issues_ids):
    jira = Jp_Jira()
    for issue_id in issues_ids:
        jira.issue(issue_id)


def render_puml(puml, height=None):
    png_data = Lambda('gw_bot.lambdas.puml_to_png').invoke({"puml": puml}).get('png_base64')
    show_png(png_data, height)

def aaaa(puml, height=None):
    return 'here 123'
    
# %load_ext autoreload
# %autoreload

# graph methods (move to separate file)

# def plot_graph(graph):
#     import networkx as nx
#     import matplotlib.pyplot as plt

#     G=nx.Graph()
#     G.add_nodes_from(graph.nodes)
#     for edge in graph.edges:
#         G.add_edge(edge[0],edge[2],label=edge[1])

#     plt.figure(figsize=(15,13))
#     #pos = nx.spring_layout(G)
#     pos=nx.nx_pydot.graphviz_layout(G)
#     nx.draw_networkx_labels(G, pos,font_size=12, font_color='white')
#     nx.draw_networkx_edge_labels(G, pos,edge_labels=nx.get_edge_attributes(G,'label'), font_color='blue')
#     nx.draw_networkx_nodes(G, pos, nodelist=None, node_size=5000, node_color='black', node_shape='o', alpha=1.0) #so^>v<dph8
#     nx.draw_networkx_edges(G, pos, edgelist=None, width=0.5, edge_color='k')

def save_graph(graph):
    return Lambda_Graph().save_gs_graph(graph)


class view:

    # helper methods
    @staticmethod
    def graph(graph, view_name, height=None):
        graph_name = Lambda_Graph().save_gs_graph(graph)
        view.show(['graph', graph_name, view_name], height)

    @staticmethod
    def go_js(graph, view_name, height=None):
        graph_name = Lambda_Graph().save_gs_graph(graph)
        view.show(['go_js', graph_name, view_name], height)

    @staticmethod
    def table(graph, view_name, height=None):
        graph_name = Lambda_Graph().save_gs_graph(graph)
        view.show(['table', graph_name, view_name], height)

    @staticmethod
    def show(params, height=200):
        browser = Lambda('osbot_browser.lambdas.lambda_browser')
        payload = {"params": params, 'data': {}}
        #browser.invoke(payload)
        png_data = browser.invoke(payload)
        # print(png_data)
        show_png(png_data, height)

    # views
    @staticmethod
    def by_issue_type(graph, height=None):
        view.graph(graph, 'by_issue_type', height)

    @staticmethod
    def by_key(graph, height=None):
        view.graph(graph, 'default', height)

    @staticmethod
    def by_rating(graph, height=None):
        view.graph(graph, 'by_rating', height)

    @staticmethod
    def by_status(graph, height=None):
        view.graph(graph, 'by_status', height)

    @staticmethod
    def no_labels(graph, height=None):
        view.graph(graph, 'no_labels', height)

    @staticmethod
    def node_label(graph, label, height=None):
        graph_name = Lambda_Graph().save_gs_graph(graph)
        view.show(['graph', graph_name, 'node_label', label], height)

    @staticmethod
    def r1_pinned(graph, height=None):
        view.graph(graph, 'r1_pinned', height)

    @staticmethod
    def r1_r4(graph, height=None):
        view.graph(graph, 'r1_r4', height)

    @staticmethod
    def table_graph(graph, height=None):
        view.table(graph, 'graph', height)

    #     @staticmethod
    #     def table_graph_all_fields(graph,height=None):
    #         view.table(graph,'graph_all_fields',height)

    @staticmethod
    def table_graph_simple(graph, height=None):
        view.table(graph, 'graph_simple', height)

    @staticmethod
    def table_graph_tasks(graph, height=None):
        view.table(graph, 'graph_tasks', height)

    @staticmethod
    def table_issue(issue_id, height=None):
        view.show(['table', issue_id, 'issue'], height)

    @staticmethod
    def circular(graph, height=None):
        view.go_js(graph, 'circular', height)

    @staticmethod
    def chord(graph, height=None):
        graph_name = Lambda_Graph().save_gs_graph(graph)
        view.show(['am_charts', graph_name, 'chord'], height)

    @staticmethod
    def mindmap(graph, height=None): view.go_js(graph, 'mindmap', height)

    @staticmethod
    def markdown(markdown): view.show(['markdown', markdown])

    @staticmethod
    def sankey(graph, height=None): view.go_js(graph, 'sankey', height)

    @staticmethod
    def swimlanes(graph, height=None): view.go_js(graph, 'swimlanes', height)

    @staticmethod
    def screenshot(url): view.show(['screenshot', url])

    @staticmethod
    def wardley_map(): view.show(['render', 'examples/wardley_map/cup-of-tea.html', 0, 0, 600, 50])

    @staticmethod
    def viva_graph(graph, height=None):
        view_name = 'default'
        graph_name = Lambda_Graph().save_gs_graph(graph)
        view.show(['viva_graph', graph_name, view_name], height)

#     @staticmethod
#     def vis_js(graph, options=None,height=200):
#         nodes = []
#         edges = []
#         for node in graph.nodes:
#             nodes.append({'id': node, 'label':node})
#         for edge in graph.edges:
#             edges.append({'from': edge[0], 'to':edge[2], 'label': edge[1]})
#         data = {'nodes': nodes, 'edges': edges, 'options': options }
#         view.show(['vis_js', json.dumps(data)],height)
