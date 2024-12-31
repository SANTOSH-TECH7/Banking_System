from flask import Flask, render_template, request, redirect
import json
from datetime import datetime
import os
from collections import defaultdict

app = Flask(__name__)

# Load data from file, if file doesn't exist create it
def load_data(file_name):
    if not os.path.exists(file_name):
        return []
    with open(file_name, 'r') as file:
        return json.load(file)

# Save data to file
def save_data(file_name, data):
    with open(file_name, 'w') as file:
        json.dump(data, file, indent=4)

# Generate Blockchain ID
def generate_blockchain_id(name, email):
    return name[:2].upper() + email[:2].upper() + str(abs(hash(name + email)))[:6]

# Initialize data from files
users = load_data('users.json')
bankers = load_data('bankers.json')
transactions = load_data('transactions.json')

# Function to count transactions per user
def count_user_transactions():
    transaction_counts = defaultdict(int)
    for transaction in transactions:
        date = transaction['timestamp'].split(' ')[0]
        sender = transaction['sender_id']
        receiver = transaction['receiver_id']
        transaction_counts[(sender, date)] += 1
        transaction_counts[(receiver, date)] += 1
    return transaction_counts

# Home page with login options
@app.route('/')
def home():
    return render_template('index.html')

# User login or registration
@app.route('/user-login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        age = request.form['age']
        address = request.form['address']
        account = request.form['account']
        branch = request.form['branch']
        blockchain_option = request.form.get('blockchain_option')

        # Generate or use provided blockchain ID
        blockchain_id = request.form['blockchain_id'] if blockchain_option == 'yes' else generate_blockchain_id(name, email)

        # Check if user already exists
        for user in users:
            if user['blockchain_id'] == blockchain_id:
                return redirect(f'/user-page/{blockchain_id}')

        # Add new user to the database
        user_data = {
            'name': name,
            'email': email,
            'age': age,
            'address': address,
            'account': account,
            'branch': branch,
            'blockchain_id': blockchain_id,
            'transactions': [],  # Initialize transactions list
        }

        users.append(user_data)
        save_data('users.json', users)

        # Notify banker of new user
        for banker in bankers:
            banker['users'].append(blockchain_id)
        save_data('bankers.json', bankers)

        return redirect(f'/user-page/{blockchain_id}')
    
    return render_template('user_login.html')

# Banker login or registration
@app.route('/banker-login', methods=['GET', 'POST'])
def banker_login():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        age = request.form['age']
        address = request.form['address']
        account = request.form['account']
        branch = request.form['branch']
        resignation = request.form['resignation']

        # Generate blockchain ID for the banker
        blockchain_id = generate_blockchain_id(name, email)

        # Check if banker already exists
        for banker in bankers:
            if banker['blockchain_id'] == blockchain_id:
                return redirect(f'/banker-page/{blockchain_id}')

        # Add new banker to the database
        banker_data = {
            'name': name,
            'email': email,
            'age': age,
            'address': address,
            'account': account,
            'branch': branch,
            'resignation': resignation,
            'blockchain_id': blockchain_id,
            'users': []
        }

        bankers.append(banker_data)
        save_data('bankers.json', bankers)

        return redirect(f'/banker-page/{blockchain_id}')
    
    return render_template('banker_login.html')

# User transaction page
@app.route('/user-page/<blockchain_id>', methods=['GET', 'POST'])
def user_page(blockchain_id):
    # Find user details using blockchain_id
    user = next((user for user in users if user['blockchain_id'] == blockchain_id), None)
    if not user:
        return "User not found!", 404

    if request.method == 'POST':
        receiver_id = request.form['receiver_id']
        amount = float(request.form['amount'])

        # Process money transfer
        transaction = {
            'sender_id': blockchain_id,
            'receiver_id': receiver_id,
            'amount': amount,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        transactions.append(transaction)
        save_data('transactions.json', transactions)

        # Notify both users of the transaction
        for usr in users:
            if usr['blockchain_id'] == blockchain_id or usr['blockchain_id'] == receiver_id:
                usr.setdefault('transactions', []).append(transaction)

        save_data('users.json', users)
        return redirect(f'/user-page/{blockchain_id}')

    return render_template('user_page.html', user=user)

# Banker transaction view page
@app.route('/banker-page/<blockchain_id>')
def banker_page(blockchain_id):
    # Find banker details using blockchain_id
    banker = next((banker for banker in bankers if banker['blockchain_id'] == blockchain_id), None)
    if not banker:
        return "Banker not found!", 404

    # Count user transactions and add to user objects
    transaction_counts = count_user_transactions()
    for user in users:
        user['transactions_count'] = transaction_counts.get((user['blockchain_id'], datetime.now().strftime('%Y-%m-%d')), 0)

    return render_template('banker_page.html', banker=banker, transactions=transactions, users=users)

if __name__ == '__main__':
    app.run(debug=True)
