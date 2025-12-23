To test with Postman:

Method: POST

URL: http://localhost:5000/extract

Body:

Select "form-data"
Key: file (change type to "File")
Value: Select your .txt file



To test only the formats.py:
example: python c.py txt_files/2310101318.txt 2310101318_output.json
python c.py input_filepath.txt outputfile_name.json
