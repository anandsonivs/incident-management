// Incident Management UI Application
class IncidentManagementApp {
    constructor() {
        this.apiBaseUrl = 'http://localhost:8000/v1';
        this.currentUser = null;
        this.incidents = [];
        this.teams = [];
        this.currentTab = 'all';
        this.filters = {
            status: '',
            team: '',
            search: ''
        };
        
        this.init();
    }

    async init() {
        await this.checkAuth();
        await this.loadTeams();
        this.setupEventListeners();
        await this.loadDashboard();
        await this.loadIncidents();
    }

    async checkAuth() {
        const token = localStorage.getItem('authToken');
        if (!token) {
            window.location.href = '/login.html';
            return;
        }

        try {
            const response = await fetch(`${this.apiBaseUrl}/users/me`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                throw new Error('Authentication failed');
            }

            this.currentUser = await response.json();
            document.getElementById('userInfo').textContent = this.currentUser.email;
        } catch (error) {
            console.error('Auth check failed:', error);
            localStorage.removeItem('authToken');
            window.location.href = '/login.html';
        }
    }

    async loadTeams() {
        try {
            const response = await this.makeRequest('/teams/');
            this.teams = response;
            
            const teamFilter = document.getElementById('teamFilter');
            teamFilter.innerHTML = '<option value="">All Teams</option>';
            
            this.teams.forEach(team => {
                const option = document.createElement('option');
                option.value = team.id;
                option.textContent = team.name;
                teamFilter.appendChild(option);
            });
        } catch (error) {
            console.error('Failed to load teams:', error);
        }
    }

    setupEventListeners() {
        // Tab switching
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });

        // Filters
        document.getElementById('statusFilter').addEventListener('change', (e) => {
            this.filters.status = e.target.value;
            this.loadIncidents();
        });

        document.getElementById('teamFilter').addEventListener('change', (e) => {
            this.filters.team = e.target.value;
            this.loadIncidents();
        });

        document.getElementById('searchInput').addEventListener('input', (e) => {
            this.filters.search = e.target.value;
            this.debounce(() => this.loadIncidents(), 300);
        });

        // Tab-specific search inputs
        document.getElementById('assignedSearchInput').addEventListener('input', (e) => {
            this.debounce(() => this.loadAssignedIncidents(), 300);
        });

        document.getElementById('acknowledgedSearchInput').addEventListener('input', (e) => {
            this.debounce(() => this.loadAcknowledgedIncidents(), 300);
        });

        document.getElementById('escalationsSearchInput').addEventListener('input', (e) => {
            this.debounce(() => this.loadEscalations(), 300);
        });

        document.getElementById('notificationsSearchInput').addEventListener('input', (e) => {
            this.debounce(() => this.loadNotifications(), 300);
        });

        // Refresh button
        document.getElementById('refreshBtn').addEventListener('click', () => {
            this.loadDashboard();
            this.loadIncidents();
            
            // Refresh current tab data
            if (this.currentTab) {
                switch (this.currentTab) {
                    case 'all':
                        this.loadIncidents();
                        break;
                    case 'assigned':
                        this.loadAssignedIncidents();
                        break;
                    case 'acknowledged':
                        this.loadAcknowledgedIncidents();
                        break;
                    case 'escalations':
                        this.loadEscalations();
                        break;
                    case 'notifications':
                        this.loadNotifications();
                        break;
                }
            }
        });

        // Modal close button
        document.getElementById('closeModal').addEventListener('click', () => {
            this.hideModal('incidentModal');
        });

        // Close modal when clicking outside
        document.getElementById('incidentModal').addEventListener('click', (e) => {
            if (e.target.id === 'incidentModal') {
                this.hideModal('incidentModal');
            }
        });

        // Event delegation for action buttons
        document.addEventListener('click', (e) => {
            // Trigger escalation button
            if (e.target.closest('.trigger-escalation-btn')) {
                const button = e.target.closest('.trigger-escalation-btn');
                const incidentId = parseInt(button.getAttribute('data-incident-id'));
                console.log('Trigger escalation button clicked for incident:', incidentId);
                this.triggerEscalation(incidentId);
            }
            
            // Acknowledge button
            if (e.target.closest('.acknowledge-btn')) {
                const button = e.target.closest('.acknowledge-btn');
                const incidentId = parseInt(button.getAttribute('data-incident-id'));
                this.acknowledgeIncident(incidentId);
            }
            
            // Resolve button
            if (e.target.closest('.resolve-btn')) {
                const button = e.target.closest('.resolve-btn');
                const incidentId = parseInt(button.getAttribute('data-incident-id'));
                this.resolveIncident(incidentId);
            }
            
            // Snooze button
            if (e.target.closest('.snooze-btn')) {
                const button = e.target.closest('.snooze-btn');
                const incidentId = parseInt(button.getAttribute('data-incident-id'));
                this.snoozeIncident(incidentId);
            }
        });

        // Create incident modal
        document.getElementById('cancelCreate').addEventListener('click', () => {
            this.hideModal('createIncidentModal');
        });

        document.getElementById('createIncidentForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.createIncident();
        });

        // Create incident button
        document.getElementById('createIncidentBtn').addEventListener('click', () => {
            this.showCreateModal();
        });

        // Logout button
        document.getElementById('logoutBtn').addEventListener('click', () => {
            localStorage.removeItem('authToken');
            window.location.href = '/login.html';
        });
    }

    async createIncident() {
        try {
            const title = document.getElementById('incidentTitle').value;
            const description = document.getElementById('incidentDescription').value;
            const severity = document.getElementById('incidentSeverity').value;
            const service = document.getElementById('incidentService').value;

            await this.makeRequest('/incidents/', {
                method: 'POST',
                body: JSON.stringify({
                    title,
                    description,
                    severity,
                    service
                })
            });

            this.hideModal('createIncidentModal');
            this.showNotification('Incident created successfully', 'success');
            
            // Reset form
            document.getElementById('createIncidentForm').reset();
            
            await this.loadDashboard();
            await this.loadIncidents();
        } catch (error) {
            console.error('Failed to create incident:', error);
            this.showNotification('Failed to create incident', 'error');
        }
    }

    showCreateModal() {
        document.getElementById('createIncidentModal').classList.remove('hidden');
    }

    async loadDashboard() {
        try {
            const response = await this.makeRequest('/incidents/');
            const incidents = response;

            // Count by status
            const counts = {
                triggered: 0,
                acknowledged: 0,
                resolved: 0,
                myIncidents: 0
            };

            incidents.forEach(incident => {
                counts[incident.status]++;
                if (incident.assignments && incident.assignments.some(a => a.user_id === this.currentUser.id)) {
                    counts.myIncidents++;
                }
            });

            // Update dashboard
            document.getElementById('triggeredCount').textContent = counts.triggered;
            document.getElementById('acknowledgedCount').textContent = counts.acknowledged;
            document.getElementById('resolvedCount').textContent = counts.resolved;
            document.getElementById('myIncidentsCount').textContent = counts.myIncidents;

        } catch (error) {
            console.error('Failed to load dashboard:', error);
            this.showNotification('Failed to load dashboard', 'error');
        }
    }

    async loadIncidents() {
        try {
            let url = '/incidents/';
            const params = new URLSearchParams();

            if (this.filters.status) params.append('status', this.filters.status);
            if (this.filters.team) params.append('team_id', this.filters.team);

            if (params.toString()) {
                url += '?' + params.toString();
            }

            const response = await this.makeRequest(url);
            this.incidents = response;

            // Filter by search term
            let filteredIncidents = this.incidents;
            if (this.filters.search) {
                const searchTerm = this.filters.search.toLowerCase();
                filteredIncidents = this.incidents.filter(incident => 
                    incident.title.toLowerCase().includes(searchTerm) ||
                    incident.description?.toLowerCase().includes(searchTerm) ||
                    incident.service?.toLowerCase().includes(searchTerm)
                );
            }

            this.renderIncidents(filteredIncidents);

        } catch (error) {
            console.error('Failed to load incidents:', error);
            this.showNotification('Failed to load incidents', 'error');
        }
    }

    async loadEscalations() {
        try {
            const container = document.getElementById('escalationsList');
            container.innerHTML = '<div class="text-center py-8"><i class="fas fa-spinner fa-spin text-blue-500 text-2xl"></i><p class="mt-2 text-gray-600">Loading escalations...</p></div>';

            // Get all escalation events
            const escalationEvents = await this.makeRequest('/escalation/events/');
            this.renderEscalations(escalationEvents);
        } catch (error) {
            console.error('Failed to load escalations:', error);
            this.showNotification('Failed to load escalations', 'error');
        }
    }

    async loadNotifications() {
        try {
            const container = document.getElementById('notificationsList');
            container.innerHTML = '<div class="text-center py-8"><i class="fas fa-spinner fa-spin text-blue-500 text-2xl"></i><p class="mt-2 text-gray-600">Loading notifications...</p></div>';

            const notifications = await this.makeRequest('/notifications/');
            this.renderNotifications(notifications);
        } catch (error) {
            console.error('Failed to load notifications:', error);
            this.showNotification('Failed to load notifications', 'error');
        }
    }

    renderEscalations(escalationEvents) {
        const container = document.getElementById('escalationsList');
        
        if (!escalationEvents || escalationEvents.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8">
                    <i class="fas fa-arrow-up text-gray-400 text-4xl mb-4"></i>
                    <p class="text-gray-500">No escalation events found</p>
                </div>
            `;
            return;
        }

        container.innerHTML = escalationEvents.map(event => {
            // Debug logging
            console.log('Escalation event timestamp:', event.created_at || event.triggered_at);
            console.log('Parsed date:', new Date(event.created_at || event.triggered_at));
            
            return `
            <div class="bg-white rounded-lg shadow p-4 border-l-4 border-orange-500">
                <div class="flex justify-between items-start mb-3">
                    <div class="flex-1">
                        <h3 class="font-medium text-gray-900">Escalation Event #${event.id}</h3>
                        <p class="text-sm text-gray-600 mt-1">Incident: ${event.incident?.title || `#${event.incident_id}`}</p>
                        ${event.incident?.service ? `<p class="text-sm text-gray-500">Service: ${event.incident.service}</p>` : ''}
                        ${event.incident?.team ? `<p class="text-sm text-gray-500">Team: ${event.incident.team.name}</p>` : ''}
                    </div>
                    <div class="text-right">
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-orange-100 text-orange-800">
                            ${event.status}
                        </span>
                        <p class="text-xs text-gray-500 mt-1">${this.getTimeAgo(event.created_at || event.triggered_at)}</p>
                    </div>
                </div>
                
                <div class="grid grid-cols-2 gap-4 text-sm">
                    <div>
                        <p class="text-gray-600"><strong>Policy:</strong> ${event.policy?.name || event.metadata?.policy_name || 'Unknown'}</p>
                        <p class="text-gray-600"><strong>Step:</strong> ${event.step + 1}</p>
                        <p class="text-gray-600"><strong>Severity:</strong> 
                            <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">
                                ${event.incident?.severity || event.metadata?.severity || 'Unknown'}
                            </span>
                        </p>
                        <p class="text-gray-600"><strong>Triggered By:</strong> ${event.metadata?.triggered_by || 'Unknown'}</p>
                    </div>
                    <div>
                        <p class="text-gray-600"><strong>Delay:</strong> ${event.metadata?.delay_minutes || 0} minutes</p>
                        <p class="text-gray-600"><strong>Incident Age:</strong> ${event.metadata?.incident_age_minutes || 0} minutes</p>
                        <p class="text-gray-600"><strong>Triggered For:</strong> ${event.metadata?.triggered_for?.join(', ') || 'Unknown'}</p>
                        <p class="text-gray-600"><strong>Completed:</strong> ${event.completed_at ? this.getTimeAgo(event.completed_at) : 'Pending'}</p>
                    </div>
                </div>
                
                ${event.metadata?.target_users ? `
                <div class="mt-3 pt-3 border-t border-gray-200">
                    <p class="text-sm font-medium text-gray-700 mb-2">Target Users:</p>
                    <div class="space-y-1">
                        ${event.metadata.target_users.map(user => `
                            <div class="flex items-center text-sm text-gray-600">
                                <i class="fas fa-user mr-2 text-gray-400"></i>
                                <span>${user.name} (${user.email})</span>
                                <span class="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                                    ${user.role}
                                </span>
                            </div>
                        `).join('')}
                    </div>
                </div>
                ` : ''}
            </div>
        `;
        }).join('');
    }

    renderNotifications(notifications) {
        const container = document.getElementById('notificationsList');
        
        if (!notifications || notifications.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8">
                    <i class="fas fa-bell text-gray-400 text-4xl mb-4"></i>
                    <p class="text-gray-500">No notifications found</p>
                </div>
            `;
            return;
        }

        container.innerHTML = notifications.map(notification => `
            <div class="bg-white rounded-lg shadow p-4 border-l-4 border-blue-500">
                <div class="flex justify-between items-start mb-3">
                    <div class="flex-1">
                        <h3 class="font-medium text-gray-900">${notification.title}</h3>
                        <p class="text-sm text-gray-600 mt-1">${notification.message}</p>
                    </div>
                    <div class="text-right">
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                            ${notification.status}
                        </span>
                        <p class="text-xs text-gray-500 mt-1">${this.getTimeAgo(notification.created_at)}</p>
                    </div>
                </div>
                
                <div class="grid grid-cols-2 gap-4 text-sm">
                    <div>
                        <p class="text-gray-600"><strong>Channel:</strong> 
                            <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                                ${notification.channel}
                            </span>
                        </p>
                        <p class="text-gray-600"><strong>Severity:</strong> 
                            <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">
                                ${notification.metadata?.severity || 'Unknown'}
                            </span>
                        </p>
                        <p class="text-gray-600"><strong>Triggered By:</strong> ${notification.metadata?.triggered_by || 'Unknown'}</p>
                        ${notification.incident_id ? `<p class="text-gray-600"><strong>Incident:</strong> #${notification.incident_id}</p>` : ''}
                    </div>
                    <div>
                        <p class="text-gray-600"><strong>Sent At:</strong> ${notification.sent_at ? this.getTimeAgo(notification.sent_at) : 'Pending'}</p>
                        <p class="text-gray-600"><strong>Role:</strong> 
                            <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800">
                                ${notification.metadata?.role || 'Unknown'}
                            </span>
                        </p>
                        <p class="text-gray-600"><strong>Delay:</strong> ${notification.metadata?.step?.delay_minutes || 0} minutes</p>
                    </div>
                </div>
                
                ${notification.metadata?.recipient ? `
                <div class="mt-3 pt-3 border-t border-gray-200">
                    <p class="text-sm font-medium text-gray-700 mb-2">Recipient:</p>
                    <div class="flex items-center text-sm text-gray-600">
                        <i class="fas fa-user mr-2 text-gray-400"></i>
                        <span>${notification.metadata.recipient.name} (${notification.metadata.recipient.email})</span>
                        <span class="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                            ${notification.metadata.recipient.role}
                        </span>
                    </div>
                </div>
                ` : ''}
            </div>
        `).join('');
    }

    async loadAssignedIncidents() {
        try {
            // Load incidents with assignments
            const response = await this.makeRequest('/incidents/?include_assignments=true');
            const allIncidents = response;
            
            // Filter incidents that are assigned to the current user
            const assignedIncidents = allIncidents.filter(incident => 
                incident.assignments && Array.isArray(incident.assignments) && incident.assignments.some(assignment => 
                    assignment.user_id === this.currentUser.id
                )
            );
            this.renderIncidents(assignedIncidents, 'assignedIncidentsList');
        } catch (error) {
            console.error('Failed to load assigned incidents:', error);
            this.showNotification('Failed to load assigned incidents', 'error');
        }
    }

    async loadAcknowledgedIncidents() {
        try {
            // Load incidents with assignments
            const response = await this.makeRequest('/incidents/?include_assignments=true');
            const allIncidents = response;
            
            // Filter incidents that are acknowledged by the current user
            const acknowledgedIncidents = allIncidents.filter(incident => 
                incident.acknowledged_at && 
                incident.assignments && 
                Array.isArray(incident.assignments) &&
                incident.assignments.some(assignment => 
                    assignment.user_id === this.currentUser.id
                )
            );
            this.renderIncidents(acknowledgedIncidents, 'acknowledgedIncidentsList');
        } catch (error) {
            console.error('Failed to load acknowledged incidents:', error);
            this.showNotification('Failed to load acknowledged incidents', 'error');
        }
    }

    renderIncidents(incidents, containerId = 'incidentsList') {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container with ID '${containerId}' not found`);
            return;
        }
        
        container.innerHTML = '';

        if (incidents.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8">
                    <i class="fas fa-inbox text-gray-400 text-4xl mb-4"></i>
                    <p class="text-gray-500">No incidents found</p>
                </div>
            `;
            return;
        }

        incidents.forEach(incident => {
            const card = this.createIncidentCard(incident);
            container.appendChild(card);
        });
    }

    createIncidentCard(incident) {
        const card = document.createElement('div');
        card.className = 'incident-card';
        card.dataset.incidentId = incident.id;

        const timeAgo = this.getTimeAgo(new Date(incident.created_at));
        const statusBadge = this.getStatusBadge(incident.status);
        const severityBadge = this.getSeverityBadge(incident.severity);
        
        // Get border color based on severity
        const borderColor = this.getSeverityBorderColor(incident.severity);

        card.innerHTML = `
            <div class="bg-white rounded-lg shadow p-4 ${borderColor}">
                <div class="flex justify-between items-start mb-3">
                    <div class="flex-1">
                        <h3 class="font-medium text-gray-900">${incident.title}</h3>
                        <p class="text-sm text-gray-600 mt-1">${incident.description || 'No description'}</p>
                        <div class="flex items-center space-x-4 text-sm text-gray-500 mt-2">
                            <span><i class="fas fa-clock mr-1"></i>${timeAgo}</span>
                            ${incident.service ? `<span><i class="fas fa-server mr-1"></i>${incident.service}</span>` : ''}
                            ${incident.team ? `<span><i class="fas fa-users mr-1"></i>${incident.team.name}</span>` : ''}
                        </div>
                    </div>
                    <div class="text-right">
                        ${statusBadge}
                        ${severityBadge}
                    </div>
                </div>
                
                <div class="flex justify-between items-center mt-3 pt-3 border-t border-gray-200">
                    <div class="flex space-x-2">
                        ${this.getActionButtons(incident)}
                    </div>
                    <button class="text-blue-600 hover:text-blue-800 text-sm font-medium" onclick="app.viewIncidentDetails(${incident.id})">
                        View Details <i class="fas fa-arrow-right ml-1"></i>
                    </button>
                </div>
            </div>
        `;

        return card;
    }

    getStatusBadge(status) {
        const statusMap = {
            'triggered': { class: 'bg-red-100 text-red-800', icon: 'exclamation-triangle', text: 'Triggered' },
            'acknowledged': { class: 'bg-yellow-100 text-yellow-800', icon: 'clock', text: 'Acknowledged' },
            'resolved': { class: 'bg-green-100 text-green-800', icon: 'check', text: 'Resolved' },
            'snoozed': { class: 'bg-gray-100 text-gray-800', icon: 'pause', text: 'Snoozed' }
        };

        const statusInfo = statusMap[status] || statusMap['triggered'];
        return `
            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusInfo.class}">
                <i class="fas fa-${statusInfo.icon} mr-1"></i>
                ${statusInfo.text}
            </span>
        `;
    }

    getSeverityBadge(severity) {
        const severityMap = {
            'critical': { class: 'bg-red-100 text-red-800', text: 'Critical' },
            'high': { class: 'bg-orange-100 text-orange-800', text: 'High' },
            'medium': { class: 'bg-yellow-100 text-yellow-800', text: 'Medium' },
            'low': { class: 'bg-green-100 text-green-800', text: 'Low' }
        };

        const severityInfo = severityMap[severity] || severityMap['medium'];
        return `
            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${severityInfo.class}">
                ${severityInfo.text}
            </span>
        `;
    }

    getSeverityBorderColor(severity) {
        const borderMap = {
            'critical': 'border-l-4 border-red-500',
            'high': 'border-l-4 border-orange-500',
            'medium': 'border-l-4 border-yellow-500',
            'low': 'border-l-4 border-green-500'
        };

        return borderMap[severity] || borderMap['medium'];
    }

    getActionButtons(incident) {
        const buttons = [];

        if (incident.status === 'triggered') {
            buttons.push(`
                <button class="btn-primary acknowledge-btn" data-incident-id="${incident.id}">
                    <i class="fas fa-check mr-1"></i>Acknowledge
                </button>
            `);
        }

        if (incident.status === 'acknowledged') {
            buttons.push(`
                <button class="btn-success resolve-btn" data-incident-id="${incident.id}">
                    <i class="fas fa-check-double mr-1"></i>Resolve
                </button>
            `);
        }

        if (incident.status !== 'resolved') {
            buttons.push(`
                <button class="btn-secondary snooze-btn" data-incident-id="${incident.id}">
                    <i class="fas fa-pause mr-1"></i>Snooze
                </button>
            `);
        }

        // Add escalation trigger button for testing
        buttons.push(`
            <button class="btn-warning trigger-escalation-btn" data-incident-id="${incident.id}">
                <i class="fas fa-arrow-up mr-1"></i>Trigger Escalation
            </button>
        `);

        return buttons.join('');
    }

    async acknowledgeIncident(incidentId) {
        try {
            await this.makeRequest(`/incidents/${incidentId}/acknowledge`, {
                method: 'POST'
            });

            this.showNotification('Incident acknowledged successfully', 'success');
            await this.loadDashboard();
            await this.loadIncidents();
        } catch (error) {
            console.error('Failed to acknowledge incident:', error);
            this.showNotification('Failed to acknowledge incident', 'error');
        }
    }

    async resolveIncident(incidentId) {
        try {
            await this.makeRequest(`/incidents/${incidentId}/resolve`, {
                method: 'POST'
            });

            this.showNotification('Incident resolved successfully', 'success');
            await this.loadDashboard();
            await this.loadIncidents();
        } catch (error) {
            console.error('Failed to resolve incident:', error);
            this.showNotification('Failed to resolve incident', 'error');
        }
    }

    async snoozeIncident(incidentId) {
        const hours = prompt('Enter number of hours to snooze:');
        if (!hours || isNaN(hours)) return;

        try {
            await this.makeRequest(`/incidents/${incidentId}/snooze?hours=${hours}`, {
                method: 'POST'
            });

            this.showNotification('Incident snoozed successfully', 'success');
            await this.loadDashboard();
            await this.loadIncidents();
        } catch (error) {
            console.error('Failed to snooze incident:', error);
            this.showNotification('Failed to snooze incident', 'error');
        }
    }

    async triggerEscalation(incidentId) {
        console.log('Trigger escalation called for incident:', incidentId);
        try {
            console.log('Making escalation request...');
            await this.makeRequest(`/escalation/incidents/${incidentId}/escalate/`, {
                method: 'POST'
            });

            console.log('Escalation request successful');
            this.showNotification('Escalation triggered successfully', 'success');
            await this.loadDashboard();
            await this.loadIncidents();
        } catch (error) {
            console.error('Failed to trigger escalation:', error);
            this.showNotification('Failed to trigger escalation', 'error');
        }
    }

    switchTab(tabName) {
        // Update tab buttons - fix the class management
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active', 'border-blue-500', 'text-blue-600');
            btn.classList.add('border-transparent', 'text-gray-500');
        });

        const activeBtn = document.querySelector(`[data-tab="${tabName}"]`);
        if (activeBtn) {
            activeBtn.classList.add('active', 'border-blue-500', 'text-blue-600');
            activeBtn.classList.remove('border-transparent', 'text-gray-500');
        }

        // Update tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.add('hidden');
            content.classList.remove('active');
        });

        const activeContent = document.getElementById(`${tabName}-tab`);
        if (activeContent) {
            activeContent.classList.remove('hidden');
            activeContent.classList.add('active');
        }

        this.currentTab = tabName;

        // Load appropriate data for each tab
        switch (tabName) {
            case 'all':
                this.loadIncidents();
                break;
            case 'assigned':
                this.loadAssignedIncidents();
                break;
            case 'acknowledged':
                this.loadAcknowledgedIncidents();
                break;
            case 'escalations':
                this.loadEscalations();
                break;
            case 'notifications':
                this.loadNotifications();
                break;
        }
    }

    showCreateModal() {
        document.getElementById('createIncidentModal').classList.remove('hidden');
    }

    async createIncident() {
        const title = document.getElementById('incidentTitle').value;
        const description = document.getElementById('incidentDescription').value;
        const severity = document.getElementById('incidentSeverity').value;
        const service = document.getElementById('incidentService').value;

        try {
            await this.makeRequest('/incidents/', {
                method: 'POST',
                body: JSON.stringify({
                    title,
                    description,
                    severity,
                    service
                })
            });

            this.hideModal('createIncidentModal');
            this.showNotification('Incident created successfully', 'success');
            
            // Reset form
            document.getElementById('createIncidentForm').reset();
            
            await this.loadDashboard();
            await this.loadIncidents();
        } catch (error) {
            console.error('Failed to create incident:', error);
            this.showNotification('Failed to create incident', 'error');
        }
    }

    hideModal(modalId) {
        document.getElementById(modalId).classList.add('hidden');
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="flex items-center">
                <i class="fas fa-${this.getNotificationIcon(type)} mr-2"></i>
                <span>${message}</span>
            </div>
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.remove();
        }, 5000);
    }

    getNotificationIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    getTimeAgo(date) {
        // Ensure we're working with a proper Date object
        const dateObj = new Date(date);
        const now = new Date();
        
        // Handle timezone properly - if the date string has timezone info, use it as is
        // Otherwise, assume it's UTC and convert to local time
        let targetDate = dateObj;
        if (isNaN(dateObj.getTime())) {
            // If parsing failed, try to parse as UTC
            targetDate = new Date(date + 'Z');
        }
        
        const diffInSeconds = Math.floor((now - targetDate) / 1000);

        if (diffInSeconds < 60) return 'Just now';
        if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
        if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
        return `${Math.floor(diffInSeconds / 86400)}d ago`;
    }

    async makeRequest(endpoint, options = {}) {
        const token = localStorage.getItem('authToken');
        const url = `${this.apiBaseUrl}${endpoint}`;

        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            }
        };

        const finalOptions = { ...defaultOptions, ...options };

        if (options.body) {
            finalOptions.body = options.body;
        }

        const response = await fetch(url, finalOptions);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    debounce(func, wait) {
        clearTimeout(this.debounceTimer);
        this.debounceTimer = setTimeout(func, wait);
    }

            async viewIncidentDetails(incidentId) {
            try {
                const incident = await this.makeRequest(`/incidents/${incidentId}`);
                const timeline = await this.makeRequest(`/incidents/${incidentId}/timeline`);
                
                // Get escalation events for this incident
                let escalationEvents = [];
                try {
                    escalationEvents = await this.makeRequest(`/escalation/incidents/${incidentId}/escalation-events/`);
                } catch (error) {
                    console.warn('Failed to load escalation events:', error);
                }
                
                // Get notifications for this incident
                let notifications = [];
                try {
                    notifications = await this.makeRequest(`/notifications/incidents/${incidentId}/notifications`);
                } catch (error) {
                    console.warn('Failed to load notifications:', error);
                }
                
                this.showIncidentModal(incident, timeline, escalationEvents, notifications);
            } catch (error) {
                console.error('Failed to load incident details:', error);
                this.showNotification('Failed to load incident details', 'error');
            }
        }

            showIncidentModal(incident, timeline, escalationEvents = [], notifications = []) {
            const modal = document.getElementById('incidentModal');
            const modalTitle = document.getElementById('modalTitle');
            const modalContent = document.getElementById('modalContent');

            modalTitle.textContent = incident.title;

            const timeAgo = this.getTimeAgo(new Date(incident.created_at));
            const statusBadge = this.getStatusBadge(incident.status);
            const severityBadge = this.getSeverityBadge(incident.severity);

            modalContent.innerHTML = `
                <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <!-- Incident Details -->
                    <div class="space-y-4">
                        <div class="bg-gray-50 p-4 rounded-lg">
                            <h4 class="font-medium text-gray-900 mb-3">Incident Information</h4>
                            <div class="space-y-2 text-sm">
                                <div class="flex justify-between">
                                    <span class="text-gray-600">Status:</span>
                                    <span>${statusBadge}</span>
                                </div>
                                <div class="flex justify-between">
                                    <span class="text-gray-600">Severity:</span>
                                    <span>${severityBadge}</span>
                                </div>
                                <div class="flex justify-between">
                                    <span class="text-gray-600">Created:</span>
                                    <span>${timeAgo}</span>
                                </div>
                                ${incident.service ? `
                                <div class="flex justify-between">
                                    <span class="text-gray-600">Service:</span>
                                    <span>${incident.service}</span>
                                </div>
                                ` : ''}
                                ${incident.team ? `
                                <div class="flex justify-between">
                                    <span class="text-gray-600">Team:</span>
                                    <span>${incident.team.name}</span>
                                </div>
                                ` : ''}
                                ${incident.resolved_at ? `
                                <div class="flex justify-between">
                                    <span class="text-gray-600">Resolved:</span>
                                    <span>${this.getTimeAgo(new Date(incident.resolved_at))}</span>
                                </div>
                                ` : ''}
                            </div>
                        </div>

                        <div class="bg-gray-50 p-4 rounded-lg">
                            <h4 class="font-medium text-gray-900 mb-3">Description</h4>
                            <p class="text-gray-700 text-sm">${incident.description || 'No description provided'}</p>
                        </div>

                        <div class="bg-gray-50 p-4 rounded-lg">
                            <h4 class="font-medium text-gray-900 mb-3">Actions</h4>
                            <div class="flex flex-wrap gap-2">
                                ${this.getActionButtons(incident)}
                            </div>
                        </div>
                    </div>

                    <!-- Timeline -->
                    <div class="space-y-4">
                        <div class="bg-gray-50 p-4 rounded-lg">
                            <h4 class="font-medium text-gray-900 mb-3">Timeline</h4>
                            <div class="space-y-3">
                                ${this.renderTimeline(timeline)}
                            </div>
                        </div>
                    </div>

                    <!-- Escalations & Notifications -->
                    <div class="space-y-4">
                        ${escalationEvents.length > 0 ? `
                        <div class="bg-gray-50 p-4 rounded-lg">
                            <h4 class="font-medium text-gray-900 mb-3">Escalations</h4>
                            <div class="space-y-3">
                                ${escalationEvents.map(event => `
                                    <div class="bg-orange-100 p-3 rounded text-sm">
                                        <div class="flex justify-between items-start mb-2">
                                            <div class="font-medium text-orange-800">Step ${event.step + 1}</div>
                                            <span class="text-xs text-orange-600">${this.getTimeAgo(new Date(event.created_at))}</span>
                                        </div>
                                        <div class="text-orange-700 mb-1">${event.metadata?.policy_name || 'Unknown Policy'}</div>
                                        <div class="text-orange-600 text-xs">
                                            <span class="font-medium">Severity:</span> ${event.metadata?.severity || 'Unknown'} | 
                                            <span class="font-medium">Delay:</span> ${event.metadata?.step?.delay_minutes || 0}m | 
                                            <span class="font-medium">Status:</span> ${event.status}
                                        </div>
                                        ${event.metadata?.target_users ? `
                                        <div class="mt-2 text-orange-600 text-xs">
                                            <span class="font-medium">Targets:</span> ${event.metadata.target_users.map(u => u.name).join(', ')}
                                        </div>
                                        ` : ''}
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                        ` : ''}
                        
                        ${notifications.length > 0 ? `
                        <div class="bg-gray-50 p-4 rounded-lg">
                            <h4 class="font-medium text-gray-900 mb-3">Notifications</h4>
                            <div class="space-y-3">
                                ${notifications.map(notification => `
                                    <div class="bg-blue-100 p-3 rounded text-sm">
                                        <div class="flex justify-between items-start mb-2">
                                            <div class="font-medium text-blue-800">${notification.title}</div>
                                            <span class="text-xs text-blue-600">${this.getTimeAgo(new Date(notification.created_at))}</span>
                                        </div>
                                        <div class="text-blue-700 mb-1">${notification.channel} | ${notification.status}</div>
                                        ${notification.metadata?.recipient ? `
                                        <div class="text-blue-600 text-xs">
                                            <span class="font-medium">To:</span> ${notification.metadata.recipient.name} (${notification.metadata.recipient.role})
                                        </div>
                                        ` : ''}
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                        ` : ''}
                    </div>
                </div>
            `;

            modal.classList.remove('hidden');
            
            // Add event listeners for action buttons in the modal
            this.setupModalActionButtons();
            
            console.log('Incident modal shown for incident:', incident.id);
        }

    renderTimeline(timeline) {
        if (!timeline || timeline.length === 0) {
            return '<p class="text-gray-500 text-sm">No timeline events</p>';
        }

        return timeline.map(event => {
            const timeAgo = this.getTimeAgo(new Date(event.created_at));
            const eventIcon = this.getTimelineEventIcon(event.event_type);
            
            return `
                <div class="flex items-start space-x-3">
                    <div class="flex-shrink-0 w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                        <i class="fas fa-${eventIcon} text-blue-600 text-sm"></i>
                    </div>
                    <div class="flex-1 min-w-0">
                        <p class="text-sm font-medium text-gray-900">${this.getTimelineEventText(event.event_type)}</p>
                        <p class="text-sm text-gray-500">${timeAgo}</p>
                        ${event.data ? `<p class="text-sm text-gray-600 mt-1">${JSON.stringify(event.data)}</p>` : ''}
                    </div>
                </div>
            `;
        }).join('');
    }

    getTimelineEventIcon(eventType) {
        const iconMap = {
            'created': 'plus-circle',
            'acknowledged': 'check-circle',
            'resolved': 'check-double',
            'assigned': 'user-plus',
            'comment_added': 'comment',
            'status_changed': 'exchange-alt',
            'escalated': 'arrow-up'
        };
        return iconMap[eventType] || 'info-circle';
    }

    getTimelineEventText(eventType) {
        const textMap = {
            'created': 'Incident Created',
            'acknowledged': 'Incident Acknowledged',
            'resolved': 'Incident Resolved',
            'assigned': 'Incident Assigned',
            'comment_added': 'Comment Added',
            'status_changed': 'Status Changed',
            'escalated': 'Incident Escalated'
        };
        return textMap[eventType] || 'Event Occurred';
    }

    setupModalActionButtons() {
        // Add event listeners for action buttons in the modal
        const modal = document.getElementById('incidentModal');
        if (!modal) return;

        // Find all action buttons in the modal
        const actionButtons = modal.querySelectorAll('button[onclick*="app."]');
        
        actionButtons.forEach(button => {
            // Remove the onclick attribute and add event listener
            const onclick = button.getAttribute('onclick');
            button.removeAttribute('onclick');
            
            if (onclick && onclick.includes('app.triggerEscalation')) {
                const incidentId = button.getAttribute('data-incident-id');
                button.addEventListener('click', () => {
                    console.log('Button clicked for incident:', incidentId);
                    this.triggerEscalation(parseInt(incidentId));
                });
            } else if (onclick && onclick.includes('app.acknowledgeIncident')) {
                const incidentId = button.getAttribute('data-incident-id');
                button.addEventListener('click', () => {
                    this.acknowledgeIncident(parseInt(incidentId));
                });
            } else if (onclick && onclick.includes('app.resolveIncident')) {
                const incidentId = button.getAttribute('data-incident-id');
                button.addEventListener('click', () => {
                    this.resolveIncident(parseInt(incidentId));
                });
            } else if (onclick && onclick.includes('app.snoozeIncident')) {
                const incidentId = button.getAttribute('data-incident-id');
                button.addEventListener('click', () => {
                    this.snoozeIncident(parseInt(incidentId));
                });
            }
        });
        
        console.log('Modal action buttons setup complete. Found', actionButtons.length, 'buttons');
    }
}

// Initialize the application
const app = new IncidentManagementApp();

// Make app globally accessible for button onclick handlers
window.app = app;
