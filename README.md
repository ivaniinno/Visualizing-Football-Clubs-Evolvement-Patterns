# Visualizing Football Clubs and Players Evolvement Patterns
A Project for Data Wrangling and Visualization Course, Spring 2025. \
This project aims to extract and emphasize key trends in worldwide club and country football, considering multiple and diverse metrics to balance outcomes quite well. Some of the included metrics are: number of club players involved in national teams, transfer balance of clubs, average age of players within a club, etc. \
Team members: **Maksim Ilin, Rail Sabirov, Ivan Ilyichev**\
The Project structure is as follows:

```
.
├── LICENSE
├── README.md
├── analysis/ # Folder contains preprocessed files with specific metrics
│   ├── average_age/
│   ├── average_points/
│   ├── club_info/
│   ├── club_titles/
│   ├── comprehensive_analysis.ipynb
│   ├── country_info/
│   ├── data_for_heatmap/ # Preprocessing files for world heatmap visualization
│   ├── legionnaires/
│   ├── players_in_national_teams/
│   ├── team_size_ratio/
│   ├── total_team_cost/
│   └── transfer_balance/
├── app/
│   ├── db/
│   ├── routes/
│   ├── app.py
│   ├── config.py
│   └── requirements.txt
├── json_to_postgresql/
│   └── psql_database.ipynb
├── parsing/
│   ├── averagePoints/
│   ├── clubImages/
│   ├── national_kader/
│   ├── parsedData/
│   ├── parse_kader/
│   ├── stars and sizeRatio Deriving/
│   ├── titles_and_cups/
│   ├── transferbalance/
│   └── transfermarktTeamsparsing/
└── web/
    └── combinedVisualizations/
        ├── Dockerfile
        ├── data/
        ├── default.conf
        ├── index.html
        ├── ball_svg.svg
        ├── scriptMap.js
        ├── scriptScatter.js
        └── styles.css
```

- "analysis" folder contains folders and file for Exploratory Data Analysis (EDA) and preprocessing for further visualizations on a frontend side.
- "web" folder contains folders and files (data, sciptScatter.js, sciptMap.js, styles.css, index.html) for two visualizations (Teams Scatter and World HeatMap). Deployed and hosted on an Innopolis University virtual machine.
- "parsing" folder contains scrapy projects for parsing all data from transfermarkt. "parsedData" folder inside contains all parsed data, that was/will be analyzed and cleaned in "analysis".
- "json_to_postgresql" contains a Jupyter notebook that converts prepared cleaned json files (from the "analysis" folder) into PostgreSQL tables. The database server is hosted on an Innopolis University virtual machine.
- "app" contains Flask API.

---
## Parsing Process

### Scrapy Framework:
- The project uses Scrapy spiders to scrape data from the transfermarkt.world website.
- Each spider is responsible for extracting specific types of data, such as average points, club images, national team rosters, transfer balances, etc.

### Data Sources:
- The spiders fetch data from structured pages on the website, using XPath or CSS selectors to extract relevant information.

### Data Processing:
- Extracted data is processed and saved into JSON files (e.g., `average_points.json`, `sorted_teams.json`).
- Additional Python scripts (e.g., `main.py`) are used to process the scraped data further, such as identifying missing years or calculating derived metrics.

### Technologies Used:
- **Python**: The primary programming language for writing spiders and processing data.
- **Scrapy**: A web scraping framework for crawling websites and extracting data.

### Output:
- The processed data is saved in JSON files, which can be used for further analysis or visualization.
---
## Analysis process

### Data Obtaining From "Parsing" Folder
- Data from "Parsing" folder were extracted and used with help of Numpy and Pandas.

### Exploratory Data Analysis
- After extracting, data were visualized to have a first glance on it with help of Matplotlib, Seaborn, and ipywidgets.

### Preprocessed Data Storing
- At the end, data were put into json files as required for further visualizations on a frontend side.

---

## Backend

### Swagger UI

- [http://10.90.137.53:5000/apidocs/](http://10.90.137.53:5000/apidocs/) **(Innopolis University Network Only)**

### Technologies Used

- **Database System**: PostgreSQL
- **Backend Framework**: Flask for core API development
- **API Documentation**: Flask-RESTx with integrated Swagger support
- **Database Connectivity**: psycopg2 for PostgreSQL integration
- **Web Server**: Gunicorn for production deployment
- **HTTP Requests**: Requests for external API interactions
- **WSGI Utilities**: Werkzeug for WSGI web application gateway

---

### Flask API

The RESTful API acts as an intermediary layer between the PostgreSQL database and frontend application, delivering data in standardized JSON format.

All routes are grouped under the ```/api``` blueprint.

### Database

Tables for the database are constructed from the pre-processed JSON format. The database is in the third normal form (3NF), which allows efficient and well-structured queries to be performed.
The database has two users: 
- The root user, who has full privileges
- The read-only user. Restricted to SELECT operations only. This account is used by the API to enforce security and prevent unintended data manipulation

The database structure is as follows:

```sql
teams (
    team_id INT PRIMARY KEY,
    team_name TEXT NOT NULL,
    number_of_cups INT,
    image_link TEXT,
    national_team_id INT REFERENCES national_teams(national_team_id)
);


national_teams (
    national_team_id INT PRIMARY KEY,
    national_team_name TEXT NOT NULL
);

team_yearly_stats (
    team_id INT REFERENCES teams(team_id),
    year INT,
    average_points DECIMAL(3,2),
    average_age DECIMAL(3,1),    
    number_of_titles_this_year INT,
    team_cost INT,
    team_size_ratio DECIMAL(4,2),
    players_in_national_team INT,
    legionnaires INT,
    transfer_balance INT,
    PRIMARY KEY (team_id, year)
);
```

---
## Web

### Deployed Product

- **With API (Innopolis University Network Only)**: [http://10.90.136.56/](http://10.90.136.56/)
- **Without API (Public)**: [https://railsab.github.io/dwProjectFootballviz/](https://railsab.github.io/dwProjectFootballviz/)

### Technologies Used

- **Frontend**: HTML, CSS, JavaScript
- **Visualization Library**: [D3.js](https://d3js.org/) for creating interactive visualizations
- **Web Server**: Nginx (configured via Docker)
- **Styling**: Custom CSS with Google Fonts integration
- **Data Formats**: JSON for data exchange

---

### Features

#### 1. **Scatter Plot Visualization**
   - Analyze club performance metrics such as:
     - Number of titles
     - Transfer balance
     - Average points per match
     - Team cost
     - Number of national team players
     - Number of legionnaires
     - Team average age
     - Team size ratio
   - Compare metrics on X and Y axes with dynamic selection.
   - View trajectories of clubs over time.
   - Clubs are represented as circles.
   - **Point Size**: The size of each point depends on the number of cups won by the club.
   - X and Y axes are dynamically adjustable.
   - Trajectories show changes over time for selected clubs.
   - **Dynamic Axis Selection**: Choose metrics for X and Y axes.
   - **Club Trajectories**: Toggle trajectory visibility for clubs over time.
   - **Country Filter**: Filter clubs by country.
   - **Detailed Club Info**: Click on a club to view its details.

#### 2. **Heatmap Visualization**
   - Explore global football metrics by country, including:
     - Average team cost
     - Total players' cost
     - Number of legionnaires
     - National team players
     - Average age of players
   - Interactive map with zoom and country selection.
   - Countries are color-coded based on selected metrics.
   - A legend dynamically updates to reflect the metric scale.
   - **Country Selection**: Click on a country to view its stats.
   - **Zoom and Pan**: Explore the map with zoom controls.
   - **Legend**: Dynamic legend for metric scales.
   - **Country-to-Scatter Navigation**: Navigate from heatmap to scatter plot for selected countries.

#### 3. **Dynamic Timeline**
   - Navigate through data across multiple years (2015–2024).
   - Play/pause timeline animations for both scatter plot and heatmap.
   - Scatter plot and heatmap update in sync with the timeline.

#### 4. **Country and Club Details**
   - View detailed information about selected countries and clubs.
   - Navigate between heatmap and scatter plot for deeper insights.

---

### How to Run

1. **Using Docker**:
   - Ensure the `data/` and `api/` endpoints are accessible.
   - Build the Docker image:
     ```bash
     docker build -t football-viz .
     ```
   - Run the container:
     ```bash
     docker run -p 80:80 football-viz
     ```
   - Open the application in your browser at `http://localhost`.

---
# What was done (checkpoint 2)
- Fixed frontend
- Configured frontend work with API
- Fixed API endpoints
- Deployed frontend and API on university VM
