__author__ = 'mnowotka'

import re
import requests
import BeautifulSoup

#-------------------------------------------------------------------------------

PAGE_REGEX = re.compile(r"&lt;&lt; &lt; (?P<current_page>\d+) of (?P<total_pages>\d+) &gt; &gt;&gt;")

REQUESTS_HEADERS = {
    'User-Agent' : 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:30.0) Gecko/20100101 Firefox/30.0',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Connection': 'keep-alive',
    'Host': 'sea.bkslab.org',
    }

#-------------------------------------------------------------------------------

def meta_redirect(content):
    print content
    soup  = BeautifulSoup.BeautifulSoup(content)

    result=soup.meta['content']
    if result:
        print result
        wait,text=result.split(";")
        if text.lower().startswith("url="):
            url=text[4:]
            return url
    print 'no result...'        
    return None

#-------------------------------------------------------------------------------

def get_similarity(smiles, identifier, descriptor, reference):
    s = requests.session()
    s.headers.update(REQUESTS_HEADERS)
    payload = {'descriptor':descriptor, 'reference':reference, 
        'smitxt': '%s %s' % (smiles, identifier)}
    url = 'http://sea.bkslab.org/search/index.php'
    r = s.get(url, allow_redirects=True)
    if r.ok:
        redirected = r.url = r.url

    s.headers.update({'Referer': redirected, 
                        'Content-Type': 'application/x-www-form-urlencoded'})
    res = s.post(url, data=payload, allow_redirects=True)
    if not res.ok:
        print "Error searching similarity, url = %s" % url
        print "payload: %s" % payload
        print "Error code: %s" % res.status_code
        print "Message: %s" % res.text
        return

    table_url = meta_redirect(res.content)
    if not table_url:
        print "no url for table..."
        return    

    print 'table_url = %s' % table_url
    res = s.get(table_url)
    
    print res.content
   
    soup = BeautifulSoup.BeautifulSoup(res.content)
    print soup.text
    table = []
    tab = soup.find("table",  {"class":"main"})

    for row in tab.findAll('tr')[1:]:
        col = row.findAll('td')
        if len(col) >= 7:
            code = col[2].string
            num_ligands = col[3].string
            ref_name = col[4].string
            e_value = col[5].string
            max_tc = col[6].string
        
            table.append((code, num_ligands, ref_name, e_value, max_tc))
    
    return table           

#-------------------------------------------------------------------------------

def main():
    usage = "usage: %prog [options] SMILES identifier"
    parser = OptionParser(usage)
    parser.add_option("-d", "--descriptor", dest="descriptor",
                      default='ecfp4', help="molecular descriptor")
    parser.add_option("-r", "--reference",
                      default='chembl16', dest="reference", 
                      help="Database to search against")
    parser.add_option("-i", "--input", default=None,
                      dest="input", help="Input file with smiles")
    parser.add_option("-o", "--output", default=None,
                      dest="output", help="Output file")

    (options, args) = parser.parse_args()
    if options.input:
        i = getFileDescriptor(options.input, 'r')
    else:
        i = None    
    if options.output:
        o = getFileDescriptor(options.output, 'w')    
    else:
        o = None
        
    if i:
        while i.readline():
            pass
    else:
                        

#-------------------------------------------------------------------------------

if __name__ == "__main__":
    main()

#-------------------------------------------------------------------------------
