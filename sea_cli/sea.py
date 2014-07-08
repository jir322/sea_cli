__author__ = 'mnowotka'

import os
import sys
import re
import hashlib
from optparse import OptionParser
import requests
import BeautifulSoup

#-------------------------------------------------------------------------------

PAGE_REGEX = re.compile(r"&lt;&lt;\s?&lt;\s?(?P<current_page>\d+) of (?P<total_pages>\d+)\s?&gt;\s?&gt;&gt;")

REQUESTS_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:30.0) Gecko/20100101 Firefox/30.0',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Connection': 'keep-alive',
    'Host': 'sea.bkslab.org',
}

#-------------------------------------------------------------------------------


def meta_redirect(content):
    soup = BeautifulSoup.BeautifulSoup(content)

    result = soup.meta['content']
    if result:
        wait, text = result.split(";")
        if text.lower().startswith("url="):
            url = text[4:]
            return url        
    return None

#-------------------------------------------------------------------------------


def get_similarity(smitxt, descriptor, reference, orderby, sort):
    s = requests.session()
    s.headers.update(REQUESTS_HEADERS)
    payload = {'descriptor': descriptor, 'reference': reference, 
               'smitxt': smitxt}
    url = 'http://sea.bkslab.org/search/index.php'
    r = s.get(url, allow_redirects=True)
    if r.ok:
        redirected = r.url
    else:
        redirected = url

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

    res = s.get(table_url)   
    soup = BeautifulSoup.BeautifulSoup(res.content)
    m = PAGE_REGEX.search(soup.text)
    if not m:
        print "can't find page number in %s" % soup.text
        return
    total_pages = int(m.groupdict().get('total_pages', '1'))
    return scrape_table(table_url, total_pages, s, orderby, sort)
    
#-------------------------------------------------------------------------------


def scrape_table(table_url, total_pages, session, orderby, sort):
    table = []
    
    for i in range(total_pages):
        payload = {'page': i, 'orderby': orderby, 'sort': sort}
        r = session.get(table_url, params=payload)
        
        if not r.ok:
            print "Error retrieving page %s, base url = %s" % (i, table_url)
            print "payload: %s" % payload
            print "Error code: %s" % r.status_code
            print "Message: %s" % r.text
            continue
        
        soup = BeautifulSoup.BeautifulSoup(r.content)        
        tab = soup.find("table",  {"class": "main"})

        for row in tab.findAll('tr')[1:]:
            col = row.findAll('td')
            if len(col) >= 7:
                num = col[1].text
                code = col[2].text
                num_ligands = col[3].text
                ref_name = col[4].text
                e_value = col[5].text
                max_tc = col[6].text
            
                table.append((num, code, num_ligands, ref_name, e_value, max_tc))
    
    return table           

#-------------------------------------------------------------------------------


def get_file_descriptor(path, mode):
    filename, file_extension = os.path.splitext(path)
    if file_extension == '.gz':
        import gzip
        return gzip.open(path, mode + 'b' if mode in ('r', 'w') else mode)
    elif file_extension == '.bz2':
        import bz2
        return bz2.BZ2File(path, mode + 'b' if mode in ('r', 'w') else mode)
    elif file_extension == '.zip':
        import zipfile
        return zipfile.ZipFile(path, mode + 'b' if mode in ('r', 'w') else mode)
    else:
        return open(path, mode + 'U' if mode == 'r' else mode)                

#-------------------------------------------------------------------------------


def write_table(smiles, table, o):
    if o:
        o.write('\n%s\n\n' % smiles)
    else:
        print '\n%s\n' % smiles

    for row in table:
        if o:
            o.write('\t'.join(row) + '\n') 
        else:
            print '\t'.join(row)
    if o:
        o.write('\n####\n')
    else:
        print '\n####'            

#-------------------------------------------------------------------------------


def get_smiles_id_pair(smiles):
    m = hashlib.md5()
    m.update(smiles)
    return "%s %s\n" % (smiles, m.hexdigest()) 

#-------------------------------------------------------------------------------


def main():
    usage = "usage: %prog [options] SMILES"
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
    parser.add_option("-b", "--order_by", default='zscore',
                      dest="order_by", help="Column to order by")
    parser.add_option("-s", "--sort", default='desc',
                      dest="sort", help="Sorting order (asc/desc)")

    (options, args) = parser.parse_args()
    if options.input:
        if not os.path.isfile(options.input):
            print "%s is not a file" % options.input
            sys.exit(1)
        i = get_file_descriptor(options.input, 'r')
    else:
        i = None    
    if options.output:
        o = get_file_descriptor(options.output, 'w')    
    else:
        o = None

    descriptor = options.descriptor
    reference = options.reference
    orderby = options.order_by
    sort = options.sort
        
    if i:
        smitxt = ''
        for line in i:
            if line.strip():
                chunk = line.strip().split()[0]
                smitxt += get_smiles_id_pair(chunk)   
            else:
                table = get_similarity(smitxt, descriptor, reference, orderby, sort)
                write_table(chunk, table, o)
                smitxt = ''
        if smitxt:
            table = get_similarity(smitxt, descriptor, reference, orderby, sort)
            write_table(chunk, table, o)            
    elif len(args) == 1:
        smitxt = get_smiles_id_pair(args[0])
        table = get_similarity(smitxt, descriptor, reference, orderby, sort)
        write_table(args[0], table, o)
    else:
        parser.print_help()   
        sys.exit(1)
    if i:
        i.close()
    if o:
        o.close()        

#-------------------------------------------------------------------------------

if __name__ == "__main__":
    main()

#-------------------------------------------------------------------------------
