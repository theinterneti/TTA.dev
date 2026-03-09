
// Graph interactivity
function filterByType(type) {
    console.log('Filtering by type:', type);
    // Filter nodes in the graph by type
    const nodes = window.currentGraph.nodes.filter(n => n.type === type);
    const nodeIds = new Set(nodes.map(n => n.id));
    const edges = window.currentGraph.edges.filter(e => 
        nodeIds.has(e.source) && nodeIds.has(e.target)
    );
    
    renderGraph({nodes, edges});
}

function searchGraph() {
    const query = document.getElementById('graphSearch').value.toLowerCase();
    if (!query) {
        renderGraph(window.currentGraph);
        return;
    }
    
    const nodes = window.currentGraph.nodes.filter(n => 
        n.name.toLowerCase().includes(query) || 
        n.type.toLowerCase().includes(query)
    );
    const nodeIds = new Set(nodes.map(n => n.id));
    const edges = window.currentGraph.edges.filter(e => 
        nodeIds.has(e.source) && nodeIds.has(e.target)
    );
    
    renderGraph({nodes, edges});
}

function showNodeDetails(nodeId) {
    const node = window.currentGraph.nodes.find(n => n.id === nodeId);
    if (!node) return;
    
    const details = document.getElementById('nodeDetails');
    details.innerHTML = `
        <h3>${node.name}</h3>
        <p><strong>Type:</strong> ${node.type}</p>
        <p><strong>File:</strong> ${node.file || 'N/A'}</p>
        <p><strong>Line:</strong> ${node.line || 'N/A'}</p>
        ${node.docstring ? `<p><strong>Docs:</strong> ${node.docstring}</p>` : ''}
    `;
    details.style.display = 'block';
}

function resetGraph() {
    document.getElementById('graphSearch').value = '';
    renderGraph(window.currentGraph);
}

// Add search on enter key
document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('graphSearch');
    if (searchInput) {
        searchInput.addEventListener('keyup', (e) => {
            if (e.key === 'Enter') searchGraph();
        });
    }
});
