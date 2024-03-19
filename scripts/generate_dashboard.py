import json


def generate_dashboard_html(data):
    services_html = ""
    for service in data:
        services_html += f"""
                <div class="col-md-4">
                    <div class="card mb-4 shadow-sm">
                        <div class="card-body">
                            <h5 class="card-title">{service['name']}</h5>
                            <p class="card-text">{service['description']}</p>
                            <a href="{service['link']}" class="btn btn-primary">Go to {service['name']}</a>
                        </div>
                    </div>
                </div>
            """

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Dashboard</title>
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
        <style>
            body {{
                padding-top: 20px;
            }}
            .container {{
                padding-top: 20px;
            }}
            .logout-button {{
                position: fixed;
                right: 20px;
                top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="text-right">
                <a href="/logout" class="btn btn-danger logout-button">Logout</a>
            </div>
            <h2 class="text-center">Welcome to Your Dashboard</h2>
            <div class="row">{services_html}</div>
        </div>
        <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.5.2/dist/umd/popper.min.js"></script>
        <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
    </body>
    </html>
        """
    return html_content


def main():
    with open("config/services_dashboard.json") as f:
        services = json.load(f)

    dashboard_html = generate_dashboard_html(services)

    with open("infrastructure/nginx_edge/html/protected/index.html", "w") as f:
        f.write(dashboard_html)

    print("Dashboard HTML generated successfully.")


if __name__ == "__main__":
    main()
