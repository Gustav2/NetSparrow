from graphviz import Digraph

def create_flutter_api_flowchart():
    # Create a new directed graph
    dot = Digraph(comment='Flutter App and API Communication Flow')
    dot.attr(rankdir='LR')  # Left to Right direction
    
    # Add nodes
    dot.attr('node', shape='box', style='rounded')
    dot.node('flutter_app', 'Flutter\nApplication')
    dot.node('api_service', 'API Service\nLayer')
    
    dot.attr('node', shape='cylinder')
    dot.node('api', 'External\nAPI')
    
    dot.attr('node', shape='box', style='rounded')
    dot.node('response', 'Response\nHandler')
    
    # Add edges with labels
    dot.edge('flutter_app', 'api_service', 'HTTP Request')
    dot.edge('api_service', 'api', 'API Call')
    dot.edge('api', 'api_service', 'JSON Response')
    dot.edge('api_service', 'response', 'Parse Data')
    dot.edge('response', 'flutter_app', 'Update UI')
    
    # Save the flowchart
    dot.render('flutter_api_flow', format='png', cleanup=True)

if __name__ == '__main__':
    create_flutter_api_flowchart()
