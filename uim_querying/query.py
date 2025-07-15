import getpass
import oracledb
import sys
# pw = getpass.getpass("Enter Password: ")

# Test to see if the cx_Oracle is recognized
print(oracledb.version)   # this returns 8.0.1 for me

# Put your instantclient folder location here (should be in the same location as your Middleware folder)
lib_dir = r"C:\oracle\instantclient_21_10"

try:
    oracledb.init_oracle_client(lib_dir=lib_dir)
except Exception as err:
    print("Error connecting: cx_Oracle.init_oracle_client()")
    print(err)
    sys.exit(1)

# UIM Login info here
dsn_tns = oracledb.makedsn('ngppnpedbadm0101.ngpp.mgmt.vf.rogers.com', '1521', service_name='QAUIM01')

connection = oracledb.connect(
    user='uimqa5',
    password='welcome1', 
    dsn=dsn_tns
)

print(connection)

cursor = connection.cursor()
# Full service name will be in the form of: CBP + '_' + SAMKEY + '_' + serviceName
fullServiceName = '820012857' + '_' + '2330766557533' + '_' + 'Gateway_CFS'
cursor = cursor.execute("select id from Service where name = '" + fullServiceName + "' order by lastmodifieddate desc fetch first 1 rows only")

for row in cursor:
    print(row)

# num_rows = 10
# while True:
#     rows = cursor.fetchmany(size=num_rows)
#     if not rows:
#         break
#     for row in rows:
#         print(row)