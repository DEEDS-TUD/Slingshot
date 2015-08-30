import MySQLdb

def main():
    connection = MySQLdb.connect(host='localhost', user='slingshot',
            passwd='slingshot', db='slingshot')

    cursor = connection.cursor()

    # Get all function signatures
    signature_query = ("""SELECT signature FROM function""")
    cursor.execute(signature_query)
    signatures = cursor.fetchall()

    tc_count = 0

    # Count entries in signature tables
    for signature in signatures:
        count_query =(""" SELECT count(*) FROM `{}`""".format(signature[0]))
        cursor.execute(count_query)
        count = cursor.fetchone()[0]
        tc_count += count

    print('Overall there are {} testcases'.format(tc_count))



if __name__ == '__main__':
    main()
