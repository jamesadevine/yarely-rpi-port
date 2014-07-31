import os, string
from os import path, getenv, makedirs

def init_html_templates(html_folder = '/tmp/pdnet_html/'):
    # Create folder to hold HTML-pages
    
    if not path.isdir(html_folder):
       makedirs(html_folder)
       
# Nifty trick from http://stackoverflow.com/questions/295135/turn-a-string-into-a-valid-filename-in-python
def validate_filename(filename):
    valid_chars = "-_.()%s%s" % (string.ascii_letters, string.digits)
    return ''.join(c for c in filename if c in valid_chars)

def black_page():
    filepath = "/tmp/pdnet_html/black_page.html"
    html = "<html><head><style>body {background-color:#000000;}</style></head><!-- Just a black page --></html>"
    f = open(filepath, 'w')
    f.write(html)
    f.close()
    return filepath

def image_page(image):
    filename = validate_filename(image.split('/')[-1])
    full_filename = '/tmp/pdnet_html/' + filename + '.html'
    html = "<html><head><style>body {background-image:url('%s'); background-repeat:no-repeat; background-position:center; background-color:#000000;}</style></head><!-- Just a black page --></html>" % image
    f = open(full_filename, 'w')
    f.write(html)
    f.close()
    return full_filename



            
