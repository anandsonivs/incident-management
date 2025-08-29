# Incident Management UI Guide

## 🎯 **Overview**

The Incident Management System now includes a comprehensive web-based user interface that provides an intuitive way to manage incidents, view escalations, and track the complete incident lifecycle.

## 🚀 **Getting Started**

### **1. Access the UI**

The UI is accessible at the root URL of your incident management system:

```bash
# Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Access the UI
http://localhost:8000/
```

### **2. Authentication**

- **Login Page**: `http://localhost:8000/login.html`
- **Main Dashboard**: `http://localhost:8000/`
- **Authentication**: JWT-based with automatic token management

## 📊 **Dashboard Overview**

### **Key Metrics**
The dashboard displays real-time statistics:

- **Triggered**: Number of active incidents
- **Acknowledged**: Incidents that have been acknowledged
- **Resolved**: Successfully resolved incidents
- **My Incidents**: Incidents assigned to the current user

### **Filters**
- **Team Filter**: Filter incidents by team
- **Status Filter**: Filter by incident status (triggered, acknowledged, resolved, snoozed)
- **Search**: Real-time search across incident titles, descriptions, and services

## 🎛️ **Tab Navigation**

### **1. All Incidents Tab**
- **Purpose**: View all incidents in the system
- **Features**:
  - Incident cards with key information
  - Status and severity badges
  - Quick action buttons (acknowledge, resolve, snooze)
  - Search and filtering capabilities
  - Create new incidents

### **2. Assigned to Me Tab**
- **Purpose**: View incidents specifically assigned to the current user
- **Features**:
  - Filtered view of personal assignments
  - Quick access to incidents requiring attention
  - Direct action buttons for assigned incidents

### **3. Acknowledged by Me Tab**
- **Purpose**: Track incidents acknowledged by the current user
- **Features**:
  - Historical view of personal acknowledgments
  - Timeline of user actions
  - Status tracking for acknowledged incidents

### **4. Escalations Tab**
- **Purpose**: Monitor escalation events and policies
- **Features**:
  - View escalation events by incident
  - Track escalation policy execution
  - Monitor escalation status (pending, completed, failed)

### **5. Notifications Tab**
- **Purpose**: View notification history
- **Features**:
  - Track sent notifications
  - Monitor notification delivery status
  - View notification content and recipients

## 🎨 **UI Components**

### **Incident Cards**
Each incident is displayed as a card with:

```html
<div class="incident-card">
    <!-- Header with title and description -->
    <h3>Incident Title</h3>
    <p>Description</p>
    
    <!-- Metadata -->
    <div class="metadata">
        <span>Time ago</span>
        <span>Service</span>
        <span>Team</span>
    </div>
    
    <!-- Status and severity badges -->
    <div class="badges">
        <span class="status-badge">Status</span>
        <span class="severity-badge">Severity</span>
    </div>
    
    <!-- Action buttons -->
    <div class="actions">
        <button>Acknowledge</button>
        <button>Resolve</button>
        <button>Snooze</button>
    </div>
</div>
```

### **Status Badges**
- **Triggered**: Red badge with exclamation icon
- **Acknowledged**: Yellow badge with clock icon
- **Resolved**: Green badge with check icon
- **Snoozed**: Gray badge with pause icon

### **Severity Badges**
- **Critical**: Red background
- **High**: Orange background
- **Medium**: Yellow background
- **Low**: Blue background

## 🔧 **User Actions**

### **Manual Acknowledgment**
Users can acknowledge incidents through explicit actions:

1. **Click "Acknowledge" button** on incident card
2. **Confirmation**: System shows success notification
3. **Status Update**: Incident status changes to "acknowledged"
4. **Timeline**: Event recorded in incident timeline

### **Incident Resolution**
1. **Click "Resolve" button** on acknowledged incidents
2. **Status Update**: Incident status changes to "resolved"
3. **Timeline**: Resolution event recorded
4. **Dashboard Update**: Counts updated in real-time

### **Incident Snoozing**
1. **Click "Snooze" button** on active incidents
2. **Enter Duration**: Specify hours to snooze
3. **Status Update**: Incident status changes to "snoozed"
4. **Auto-Resume**: Incident returns to previous status after snooze period

### **Creating Incidents**
1. **Click "Create Incident" button**
2. **Fill Form**:
   - Title (required)
   - Description
   - Severity (low, medium, high, critical)
   - Service name
3. **Submit**: Incident created and appears in list

## 📱 **Responsive Design**

The UI is fully responsive and works on:

- **Desktop**: Full feature set with side-by-side layouts
- **Tablet**: Optimized layout with stacked components
- **Mobile**: Touch-friendly interface with simplified navigation

### **Mobile Features**
- Swipe gestures for navigation
- Touch-optimized buttons
- Collapsible sections
- Mobile-friendly modals

## 🎨 **Theme and Customization**

### **Color Scheme**
- **Primary**: Blue (#3B82F6)
- **Success**: Green (#10B981)
- **Warning**: Yellow (#F59E0B)
- **Error**: Red (#EF4444)
- **Info**: Gray (#6B7280)

### **Dark Mode Support**
The UI includes dark mode support that automatically activates based on system preferences:

```css
@media (prefers-color-scheme: dark) {
    .incident-card {
        @apply bg-gray-800 border-gray-700 text-white;
    }
}
```

## 🔒 **Security Features**

### **Authentication**
- JWT token-based authentication
- Automatic token refresh
- Secure token storage in localStorage
- Automatic logout on token expiration

### **Authorization**
- Role-based access control
- Team-based incident visibility
- User-specific action permissions

## 📊 **Real-time Updates**

### **Auto-refresh**
- Dashboard metrics update automatically
- Incident lists refresh periodically
- Real-time status changes

### **Notifications**
- Success/error notifications for actions
- Toast-style notifications
- Auto-dismiss after 5 seconds

## 🚀 **Performance Features**

### **Optimizations**
- Debounced search input (300ms delay)
- Lazy loading of incident details
- Efficient DOM updates
- Minimal API calls

### **Caching**
- Local storage for user preferences
- Session-based data caching
- Optimistic UI updates

## 🔧 **Technical Implementation**

### **Frontend Stack**
- **HTML5**: Semantic markup
- **CSS3**: Tailwind CSS for styling
- **JavaScript**: Vanilla JS with ES6+ features
- **Icons**: Font Awesome 6.0

### **API Integration**
- RESTful API calls
- JSON data format
- Error handling
- Loading states

### **File Structure**
```
app/frontend/
├── index.html          # Main dashboard
├── login.html          # Login page
├── styles.css          # Custom styles
└── app.js             # Main application logic
```

## 🎯 **User Workflows**

### **Typical Incident Response Flow**

1. **Incident Detection**
   - Elastic APM triggers alert
   - Incident created automatically
   - Appears in "All Incidents" tab

2. **Initial Response**
   - User sees incident in dashboard
   - Reviews incident details
   - Clicks "Acknowledge" button

3. **Investigation**
   - User adds comments
   - Updates incident status
   - Assigns to team members

4. **Resolution**
   - User clicks "Resolve" button
   - Incident marked as resolved
   - Timeline updated

### **Escalation Monitoring**

1. **View Escalations Tab**
   - See all escalation events
   - Monitor policy execution
   - Track escalation status

2. **Escalation Details**
   - View escalation steps
   - Check completion status
   - Review escalation history

## 🔍 **Troubleshooting**

### **Common Issues**

1. **Login Problems**
   - Check API server is running
   - Verify credentials
   - Clear browser cache

2. **Incidents Not Loading**
   - Check network connection
   - Verify API endpoints
   - Check browser console for errors

3. **Actions Not Working**
   - Verify user permissions
   - Check incident status
   - Review API responses

### **Browser Compatibility**
- **Chrome**: 80+
- **Firefox**: 75+
- **Safari**: 13+
- **Edge**: 80+

## 🚀 **Future Enhancements**

### **Planned Features**
- Real-time WebSocket updates
- Advanced filtering and sorting
- Bulk incident operations
- Export functionality
- Mobile app version
- Advanced analytics dashboard

### **Customization Options**
- Custom themes
- Configurable dashboards
- User preferences
- Team-specific views

This comprehensive UI provides an intuitive and powerful interface for managing incidents, with full support for manual acknowledgment and complete incident lifecycle tracking! 🎯
