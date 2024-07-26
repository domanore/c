from flask import Flask, request, jsonify, render_template_string, redirect
from threading import Thread
from queue import Queue
import time

app = Flask(__name__)

# Simulated database for showtimes, seat availability, and seating formation
showtimes = {
    "2024-06-26 10:00": {
        "movie": "Galaksi Jauh: Petualangan Antar Bintang",
        "seats": {f"{row}{num}": True for row in "ABCDE" for num in range(1, 11)},
        "sold_tickets": 0,
        "max_tickets": 50,
        "formation": "teater"
    },
    "2024-06-26 13:00": {
        "movie": "Legenda Raja Laut: Kembalinya Sang Pahlawan",
        "seats": {f"{row}{num}": True for row in "ABCDE" for num in range(1, 11)},
        "sold_tickets": 0,
        "max_tickets": 50,
        "formation": "arena"
    },
    "2024-06-26 16:00": {
        "movie": "Misteri Pulau Hantu",
        "seats": {f"{row}{num}": True for row in "ABCDE" for num in range(1, 11)},
        "sold_tickets": 0,
        "max_tickets": 50,
        "formation": "lurus"
    },
    "2024-06-26 19:00": {
        "movie": "Petualangan Waktu: Mesin Penjelajah Masa",
        "seats": {f"{row}{num}": True for row in "ABCDE" for num in range(1, 11)},
        "sold_tickets": 0,
        "max_tickets": 50,
        "formation": "vip"
    }
}

# Booking history
booking_history = []

# FIFO Queue for booking requests
booking_queue = Queue()

# Function to process booking requests from the queue
def process_booking_queue():
    while True:
        if not booking_queue.empty():
            booking_request = booking_queue.get()
            response = process_booking(booking_request)
            booking_queue.task_done()
            print(response)  # Optional: Print response to the console for debugging
        time.sleep(1)

# Function to process a single booking request
def process_booking(data):
    showtime = data.get('showtime')
    seat = data.get('seat')
    name = data.get('name')

    if not showtime or not seat or not name:
        return {"status": "error", "message": "Missing booking information."}

    if showtimes[showtime]["sold_tickets"] >= showtimes[showtime]["max_tickets"]:
        return {"status": "error", "message": "Maximum number of tickets sold for this showtime."}

    if not showtimes[showtime]["seats"].get(seat, False):
        return {"status": "error", "message": "Seat already booked or invalid seat."}

    showtimes[showtime]["seats"][seat] = False
    showtimes[showtime]["sold_tickets"] += 1
    booking_history.append({
        "name": name,
        "movie": showtimes[showtime]["movie"],
        "showtime": showtime,
        "seat": seat,
        "purchase_date": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    })
    return {"status": "success", "message": "Seat successfully booked!", "movie": showtimes[showtime]["movie"]}

@app.route('/')
def index():
    showtimes_html = generate_showtimes_html()
    history_html = generate_history_html()
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Movie Ticket Booking System</title>
        <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
        <style>
            body {
                font-family: 'Roboto', sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f4f4f9;
            }
            h1, h2, h3 {
                text-align: center;
                color: #333;
            }
            #showtimes {
                display: flex;
                flex-wrap: wrap;
                justify-content: center;
                gap: 20px;
            }
            .showtime {
                border: 1px solid #ccc;
                border-radius: 8px;
                padding: 20px;
                background-color: #fff;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                max-width: 300px;
                width: 100%;
                transition: transform 0.3s, box-shadow 0.3s;
                cursor: pointer;
                text-align: center;
                position: relative;
            }
            .showtime:hover {
                transform: scale(1.05);
                box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
            }
            .seats {
                display: flex;
                flex-direction: column;
                gap: 10px;
                margin-top: 10px;
            }
            .seat-row {
                display: flex;
                justify-content: center;
                gap: 5px;
            }
            .seat {
                padding: 10px;
                font-size: 14px;
                cursor: pointer;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                transition: background-color 0.3s;
                width: 30px;
                height: 30px;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .seat:disabled {
                background-color: #ccc;
                cursor: not-allowed;
            }
            .seat:not(:disabled):hover {
                background-color: #45a049;
            }
            #notification {
                margin-top: 20px;
                text-align: center;
                color: #e74c3c;
            }
            #booking-history {
                margin-top: 20px;
                text-align: center;
            }
            #booking-history table {
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                font-size: 18px;
                text-align: left;
            }
            #booking-history table thead tr {
                background-color: #f2f2f2;
                text-align: left;
            }
            #booking-history table th, #booking-history table td {
                padding: 12px 15px;
            }
            #booking-history table th {
                background-color: #f2f2f2;
            }
            #booking-history table tbody tr {
                border-bottom: 1px solid #dddddd;
            }
            #booking-history table tbody tr:nth-of-type(even) {
                background-color: #f3f3f3;
            }
            #booking-history table tbody tr:last-of-type {
                border-bottom: 2px solid #009879;
            }
            #booking-history table tbody tr.active-row {
                font-weight: bold;
                color: #009879;
            }
            .select-button {
                padding: 10px 20px;
                font-size: 16px;
                cursor: pointer;
                background-color: #007BFF;
                color: white;
                border: none;
                border-radius: 4px;
                transition: background-color 0.3s;
                margin-top: 10px;
            }
            .select-button:hover {
                background-color: #0056b3;
            }
            .seat-plan {
                display: none;
                flex-direction: column;
                align-items: center;
                margin-top: 10px;
                background-color: #f9f9f9;
                padding: 10px;
                border-radius: 8px;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                max-width: 280px;
            }
            .seat-plan.active {
                display: flex;
            }
            .showtime-details {
                position: absolute;
                top: 10px;
                left: 10px;
                font-size: 12px;
                color: #666;
            }
            #delete-booking {
                margin-top: 20px;
                text-align: center;
            }
        </style>
    </head>
    <body>
        <h1>Movie Ticket Booking System</h1>
        <h2>Select a Showtime</h2>
        <div id="showtimes">
            {{ showtimes_html|safe }}
        </div>
        <div id="notification"></div>
        <div id="booking-history">
            <h2>Booking History</h2>
            {{ history_html|safe }}
        </div>
        <div id="delete-booking">
            <h3>Delete Booking</h3>
            <form id="delete-booking-form">
                <input type="text" id="delete-name" placeholder="Enter your name">
                <button type="button" onclick="deleteBooking()">Delete</button>
            </form>
        </div>
        <script>
            function selectSeat(seatButton, showtime, seat) {
                const name = prompt("Enter your name:");
                if (!name) return;

                fetch('/book', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ showtime, seat, name })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        seatButton.disabled = true;
                        seatButton.style.backgroundColor = '#ccc';
                        document.getElementById('notification').textContent = data.message + ' - ' + data.movie;
                    } else {
                        document.getElementById('notification').textContent = data.message;
                    }
                })
                .catch(error => console.error('Error:', error));
            }

            function toggleSeatPlan(button) {
                const seatPlan = button.nextElementSibling;
                seatPlan.classList.toggle('active');
            }

            function deleteBooking() {
                const name = document.getElementById('delete-name').value;
                if (!name) {
                    alert("Please enter your name.");
                    return;
                }

                fetch('/delete', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ name })
                })
                .then(response => response.json())
                .then(data => {
                    document.getElementById('notification').textContent = data.message;
                    if (data.status === 'success') {
                        setTimeout(() => {
                            window.location.reload();
                        }, 2000);
                    }
                })
                .catch(error => console.error('Error:', error));
            }
        </script>
    </body>
    </html>
    ''', showtimes_html=showtimes_html, history_html=history_html)

@app.route('/book', methods=['POST'])
def book():
    data = request.get_json()
    booking_queue.put(data)
    return jsonify({"status": "queued", "message": "Booking request has been queued."})

@app.route('/delete', methods=['POST'])
def delete_booking():
    data = request.get_json()
    name = data.get('name')
    if not name:
        return jsonify({"status": "error", "message": "Name is required."})

    initial_length = len(booking_history)
    booking_history[:] = [booking for booking in booking_history if booking["name"] != name]

    if len(booking_history) == initial_length:
        return jsonify({"status": "error", "message": "No bookings found with the given name."})

    for showtime in showtimes.values():
        for seat, availability in showtime["seats"].items():
            if availability == False:
                showtime["seats"][seat] = True
                showtime["sold_tickets"] -= 1

    return jsonify({"status": "success", "message": "Booking deleted successfully."})

def generate_showtimes_html():
    html = ""
    for time, details in showtimes.items():
        seats_html = ""
        for row in "ABCDE":
            seats_html += '<div class="seat-row">'
            for num in range(1, 11):
                seat_id = f"{row}{num}"
                disabled = "disabled" if not details["seats"][seat_id] else ""
                seats_html += f'<button class="seat" {disabled} onclick="selectSeat(this, \'{time}\', \'{seat_id}\')">{seat_id}</button>'
            seats_html += '</div>'
        
        html += f'''
        <div class="showtime">
            <div class="showtime-details">
                <strong>{details["movie"]}</strong><br>
                Showtime: {time}
            </div>
            <button class="select-button" onclick="toggleSeatPlan(this)">Select Seats</button>
            <div class="seat-plan">
                {seats_html}
            </div>
        </div>
        '''
    return html

def generate_history_html():
    if not booking_history:
        return "<p>No bookings found.</p>"
    
    html = "<table><thead><tr><th>Name</th><th>Movie</th><th>Showtime</th><th>Seat</th><th>Purchase Date</th></tr></thead><tbody>"
    for booking in booking_history:
        html += f"<tr><td>{booking['name']}</td><td>{booking['movie']}</td><td>{booking['showtime']}</td><td>{booking['seat']}</td><td>{booking['purchase_date']}</td></tr>"
    html += "</tbody></table>"
    return html

# Start the booking processing thread
Thread(target=process_booking_queue, daemon=True).start()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
