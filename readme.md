# PagesJaunes.ca Business Contact Scraper

A Python script that scrapes business contact information from PagesJaunes.ca and exports the results to CSV format.

## Features

🔍 **Search Functionality**
- Search PagesJaunes.ca with any keyword or business type
- Optional location filtering
- Configurable number of pages to scrape (default: 5)

📊 **Data Extraction**
- Company Name
- Phone Number
- Website URL (if available)
- Email Address (extracted from business websites)

🛡️ **Anti-Detection Features**
- Random User-Agent rotation
- Random delays between requests
- Retry mechanism for failed requests
- Respectful scraping practices

## Installation

### Prerequisites
- Python 3.7 or higher
- pip (Python package installer)

### Setup

1. **Clone or download the script files**
   ```bash
   # Download the files to your desired directory
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

   Or install manually:
   ```bash
   pip install requests beautifulsoup4 pandas lxml openpyxl
   ```

## Usage

### Command Line Interface

#### Basic Usage (Interactive Mode)
```bash
python pagesjaunes_scraper.py
```
The script will prompt you for:
- Search term (e.g., "Firme avocat Rive-Nord")
- Location (optional)

#### Advanced Usage (Command Line Arguments)
```bash
# Basic search
python pagesjaunes_scraper.py --query "Firme avocat Rive-Nord"

# Search with location
python pagesjaunes_scraper.py --query "Restaurant" --location "Montreal"

# Custom number of pages and output file
python pagesjaunes_scraper.py --query "Dentist" --pages 10 --output "dentists.csv"

# Full example
python pagesjaunes_scraper.py -q "Plombier" -l "Quebec" -p 3 -o "plumbers_quebec.csv"
```

### Command Line Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--query` | `-q` | Search query/keyword | Interactive prompt |
| `--location` | `-l` | Location filter | None |
| `--pages` | `-p` | Number of pages to scrape | 5 |
| `--output` | `-o` | Output CSV filename | Auto-generated |

## Example Output

### Sample CSV Structure
```csv
Company Name,Phone Number,Website URL,Email Address
Avocats Rive-Nord Inc,514-555-1234,https://www.avocatsrn.ca,info@avocatsrn.ca
Cabinet Juridique Laval,(450) 555-5678,https://www.cabinetlaval.com,contact@cabinetlaval.com
Maître Dupont Avocats,514-555-9999,,
```

### Console Output Example
```
🔍 Searching for: 'Firme avocat Rive-Nord'
📍 Location: ''
📄 Output file: 'firme_avocat_rive_nord.csv'
📖 Pages to scrape: 5
--------------------------------------------------
2024-01-15 10:30:15 - INFO - Searching page 1 for 'Firme avocat Rive-Nord'...
2024-01-15 10:30:18 - INFO - Found 15 businesses
2024-01-15 10:30:18 - INFO - Extracting email addresses from websites...
2024-01-15 10:30:25 - INFO - Saved 15 businesses to firme_avocat_rive_nord.csv

📊 SCRAPING SUMMARY
==================================================
Total businesses found: 15
Businesses with websites: 12
Businesses with emails: 8
Results saved to: firme_avocat_rive_nord.csv
```

## Technical Details

### Dependencies
- **requests**: HTTP library for web scraping
- **beautifulsoup4**: HTML parsing library
- **pandas**: Data manipulation and CSV export
- **lxml**: XML/HTML parser (optional, improves performance)
- **openpyxl**: Excel file support (for future Excel export feature)

### Email Extraction
The script uses the following regex pattern to find email addresses:
```python
r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
```

### Anti-Detection Measures
1. **User-Agent Rotation**: Randomly selects from 5 different browser User-Agents
2. **Request Delays**: Random delays between 1-3 seconds between pages
3. **Retry Logic**: Up to 3 retry attempts for failed requests
4. **Respectful Scraping**: Implements delays and limits to avoid overwhelming the server

## Error Handling

The script includes comprehensive error handling for:
- Network connection issues
- Invalid search queries
- Website parsing errors
- File writing permissions
- Keyboard interruption (Ctrl+C)

## Limitations

1. **Website Structure**: PagesJaunes.ca may change their HTML structure, requiring script updates
2. **Rate Limiting**: The site may implement rate limiting; adjust delays if needed
3. **Email Detection**: Not all business websites contain easily accessible email addresses
4. **Geographic Scope**: Primarily designed for Canadian businesses on PagesJaunes.ca

## Troubleshooting

### Common Issues

1. **No results found**
   - Try broader search terms
   - Check spelling of search query
   - Verify PagesJaunes.ca is accessible

2. **Import errors**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Check Python version (3.7+ required)

3. **Permission errors**
   - Run with appropriate file permissions
   - Ensure output directory is writable

4. **Network errors**
   - Check internet connection
   - Try reducing the number of pages (`--pages` option)
   - Increase delays by modifying `delay_range` in the script

### Debug Mode
For debugging, you can enable more verbose logging by modifying the logging level in the script:
```python
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
```

## Legal Considerations

- This script is for educational and research purposes
- Respect PagesJaunes.ca's terms of service and robots.txt
- Use reasonable delays between requests
- Consider reaching out to PagesJaunes.ca for bulk data needs
- Be mindful of data privacy and GDPR/privacy regulations when handling scraped data

## Contributing

Feel free to submit improvements, bug fixes, or feature requests. Some potential enhancements:
- Excel export functionality
- GUI interface
- Additional search filters
- Database storage options
- Multi-threading for faster scraping

## License

This script is provided as-is for educational purposes. Use responsibly and in accordance with applicable laws and website terms of service.
