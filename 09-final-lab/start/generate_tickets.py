import json
import random
from datetime import datetime, timedelta
from csv import DictWriter

# Database connection configuration
DB_CONFIG = {
    "dbname": "pgvector",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",  # Change if using Docker, e.g., "db"
    "port": "5050"  # Ensure this matches your PostgreSQL setup
}

# Sample support issue templates
ISSUE_TEMPLATES = [
    "User cannot log in, receiving authentication error.",
    "Email notifications are not being sent to customers.",
    "VPN connection drops intermittently for remote workers.",
    "Application crashes when submitting a form.",
    "Payment processing fails for international customers.",
    "Slow loading times on the website homepage.",
    "Database connection errors occur randomly.",
    "Users unable to reset passwords via the portal.",
    "File uploads fail with unknown error message.",
    "Mobile app freezes when navigating to settings."
]

# Status options
STATUS_OPTIONS = ["open", "resolved", "in_progress"]

# Priority levels
PRIORITY_OPTIONS = ["low", "medium", "high", "critical"]

# Sample JSONB metadata
TAGS_OPTIONS = [
    ["authentication", "login"],
    ["email", "notifications"],
    ["network", "VPN"],
    ["performance", "loading"],
    ["payments", "transactions"],
    ["database", "connectivity"],
    ["user-management", "password-reset"],
    ["uploads", "file-management"],
    ["mobile", "app-crash"],
    ["security", "data-protection"]
]

RESOLUTION_STEPS = {
    "authentication": ["Reset password", "Check logs", "Verify MFA settings"],
    "email": ["Check email server settings", "Verify SMTP configuration"],
    "network": ["Restart router", "Check ISP", "Update VPN client"],
    "performance": ["Optimize database queries", "Increase server resources"],
    "payments": ["Check payment gateway logs", "Verify card details"],
    "database": ["Restart DB service", "Check connection pool"],
    "user-management": ["Ensure user exists", "Check permission settings"],
    "uploads": ["Increase file size limit", "Check file format"],
    "mobile": ["Update app version", "Clear cache", "Reinstall app"],
    "security": ["Run vulnerability scan", "Check firewall rules"]
}

# Generate a random support ticket
def generate_support_ticket():
    issue = random.choice(ISSUE_TEMPLATES)
    status = random.choice(STATUS_OPTIONS)
    priority = random.choice(PRIORITY_OPTIONS)
    
    tags = random.choice(TAGS_OPTIONS)
    resolution_steps = sum([RESOLUTION_STEPS[tag] for tag in tags if tag in RESOLUTION_STEPS], [])

    metadata = {
        "tags": tags,
        "resolution_steps": resolution_steps,
        "reported_at": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
        "last_updated": datetime.now().isoformat()
    }

    return {
        "issue_description": issue,
        "status": status,
        "priority": priority,
        "metadata": json.dumps(metadata)  # Convert dict to JSON string for PostgreSQL
    }

# Insert generated tickets into PostgreSQL
def insert_tickets_into_db(num_tickets=10):

    tickets = [generate_support_ticket() for _ in range(num_tickets)]

    with open("tickets.csv", "w") as file:
      
      fields = ["issue_description", "status", "priority", "metadata"]
      writer = DictWriter(file, fieldnames=fields)
      writer.writeheader()
      for ticket in tickets:
        writer.writerow(ticket)
    print(f"✅ Successfully created {num_tickets} support tickets!")

# Run the script
if __name__ == "__main__":
    insert_tickets_into_db(num_tickets=500)  # Generate & insert 20 tickets
