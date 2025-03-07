from lxml import etree
from random import randint, choice
import string
import requests

# TODO MAKE THIS WHOLE PROGRAM A CLASS TO MAKE IT EASIER / CLEANER TO PASS AROUND THE ROOT NODE

class createOrder:
    def __init__(self, root, nsmap):
        self.root = root
        self.nsmap = nsmap

    def submitOrder(self, url, order, username = 'admin', password = 'welcome1'):
        # FIX THIS FUNCTION LATER MAYBE
        url="http://osmdev1-z1.ngpp.mgmt.vf.rogers.com:7001/OrderManagement/wsapi"
        #headers = {'content-type': 'application/soap+xml'}
        headers = {'content-type': 'text/xml'}
        body = f"""
                <soapenv:Envelope xmlns:techord="http://xmlns.oracle.com/EnterpriseObjects/Core/EBO/TechnicalOrder/V1" xmlns:corecom="http://xmlns.oracle.com/EnterpriseObjects/Core/Common/V2" xmlns:ebo="http://xmlns.oracle.com/EnterpriseObjects/Core/EBO/TechnicalOrder/V1" xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd" xmlns:ws="http://xmlns.oracle.com/communications/ordermanagement" xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
                    <soapenv:Header>
                        <wsse:Security>
                            <wsse:UsernameToken>
                                <wsse:Username>{username}</wsse:Username>
                                <wsse:Password Type="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordText">{password}</wsse:Password>
                            </wsse:UsernameToken>
                        </wsse:Security>
                    </soapenv:Header>
                    <soapenv:Body>
                        <ws:CreateOrder>
                            {order}
                        </ws:CreateOrder>
                    </soapenv:Body>
                </soapenv:Envelope>
        """

        response = requests.post(url,data=body,headers=headers)
        print(response.content)

    def prettyprint(self, elements, **kwargs):
        for element in elements:
            xml = etree.tostring(element, pretty_print=True, **kwargs)
            print(xml.decode(), end='')
            print("\n\n")


    def numberGen(self, n) -> int:
        range_start = 10 ** (n-1) 
        range_end = (10 ** n) - 1

        return randint(range_start, range_end)

    def id_generator(self, size, chars = string.ascii_uppercase + string.digits):
        # Check the requirements for serial number and mac address formatting
        return ''.join(choice(chars) for _ in range(size))

    def replace(self, elements, length) -> None:

        # Look at the first elements text, check if the first character is numeric (is a number), if so True, else False
        ishhid = False if elements[0].text[:1].isnumeric() else True
        count = 0

        print("Old value: ", elements[0].text)
        if ishhid:
            cbp = self.getCBP()
            length -= len(cbp)
            print("Length: ", length)
            new_value = self.numberGen(length)
            for element in elements:
                element.text = element.text[:1] + cbp + str(new_value) # Keep the letter (first character of the hhid) and replace all numbers after
                count += 1
        else:
            print("Length: ", length)
            new_value = self.numberGen(length)
            for element in elements:
                element.text = str(new_value)
                count += 1

        print("New value: ", elements[0].text)
        print("Number of values changed: ", count)
        print("\n")
        
    def getCBP(self):
        return self.root.xpath("//a:customer/a:Id[text()]", namespaces = self.nsmap)[0].text

    def orderIdReplace(self):
        # CHECK IF THE ORDER ID'S WILL EVER BE IN ANOTHER PLACE

        rbt_characteristics = self.root.xpath("//a:ProductOrder/a:orderItems/a:RBTCharacteristics[a:name[text()='OrderID'] and a:value[normalize-space() != '']]", namespaces = self.nsmap)
        if len(rbt_characteristics):
            old_orderId_element = rbt_characteristics[0].xpath("./a:value", namespaces = self.nsmap)
            old_orderId = old_orderId_element[0].text

            order_ids = self.retrieveValues(rbt_characteristics)

            self.replace(order_ids, len(old_orderId))
        
        
    def retrieveValues(self, parent) -> list:
        ret = []
        for element in parent:
            ret.append(element.xpath("./a:value", namespaces = self.nsmap)[0])
        
        return ret

    def samkeyReplace(self) -> None:
        samKey_parent = self.root.xpath("//a:RBTCharacteristics[a:name[text()='SamKey'] and a:value[normalize-space() != '']]"  
                                + "| //a:characteristicValues[a:name[text()='SamKey'] and a:value[normalize-space() != '']]", namespaces = self.nsmap)
        if len(samKey_parent):
            samkeys = self.retrieveValues(samKey_parent)
            self.replace(samkeys, len(samkeys[0].text))


    def cbpReplace(self) -> None:
        # Will this always only be in the customer elements
        # Do I need to change the registration key? As part of it is built with the CBP
        cbp_parent = self.root.xpath("//a:customer/a:Id[text()]", namespaces = self.nsmap)

        if len(cbp_parent):
            old_cbp = cbp_parent[0].text
            self.replace(cbp_parent, len(old_cbp))
        

    def workIdReplace(self) -> None:
        workId_parent = self.root.xpath("//a:RBTCharacteristics[a:name[text()='WorkOrderId'] and a:value[normalize-space() != '']]", namespaces = self.nsmap)
        if len(workId_parent):
            workIds = self.retrieveValues(workId_parent)
            old_workId = workIds[0].text
            self.replace(workIds, len(old_workId))

    def hhidReplace(self) -> None:
        # Always call after cbp has already been replaced with new value
        hhid_parent = self.root.xpath("//a:RBTCharacteristics[a:name[text()='HHID'] and a:value[normalize-space() != '']]", namespaces = self.nsmap)
        if len(hhid_parent):
            hhids = self.retrieveValues(hhid_parent)
            old_hhid = hhids[0].text
            self.replace(hhids, len(old_hhid) - 1) # Subtract 1 from the length for letter at the beginning

    def serialAndMacReplace(self) -> None:
        # Do I need to change all these mac addresses?
        serial_parent = self.root.xpath("//a:characteristicValues[a:name[text()='Serial_Number' or contains(text(), ('MAC_Address')) or contains(text(), ('Mac_Address'))]" 
                                        + " and a:value[normalize-space() != '']]", namespaces = self.nsmap)
        count = 0

        # self.prettyprint(serial_parent)
        if len(serial_parent):
            vals_to_change = []
            for element in serial_parent:
                vals_to_change.append(element.xpath("./a:name", namespaces = self.nsmap)[0].text)

            print(f"Element Values to Change: {vals_to_change}\n")

            serial_numbers = self.retrieveValues(serial_parent)

            for serial_number in serial_numbers:
                length = len(serial_number.text)
                print("Old value: ", serial_number.text)
                serial_number.text = self.id_generator(length) # If the value is 'NA' replace?
                count += 1
                
                print("New value: ", serial_number.text)

            print("Number of values changed: ", count)
            print("\n")

    def affectedProductReplace(self) -> None:
        # Do I need to replace roleReceiver as well?
        # What about REF_AP_ID??

        ap_parent = self.root.xpath("//a:affectedProduct", namespaces = self.nsmap)

        # Change both affected product id and APID value to the same number for each affectd product
        for element in ap_parent:
            id = element.xpath("./a:ID", namespaces = self.nsmap)
            ap_id = element.xpath("./a:characteristicValues[a:name[text()='APID']]", namespaces = self.nsmap)
            
            if len(id) and len(ap_id):
                new_id = self.numberGen(len(id[0].text))
                print(f"Old id: {id[0].text}")
                id[0].text = str(new_id)
                ap_id[0].text = str(new_id)
                print(f"New id: {new_id}\n")


    def orderItemIdReplace(self):
        # TODO Figure out the correct format for reference numbers (9 Numbers and then a Letter?)

        orderItems = self.root.xpath("//a:orderItems", namespaces = self.nsmap)
        old_OIRefs = {}
        if len(orderItems):
            for element in orderItems:
                print("\nNew Order Item")
                
                # Has orderItemReferenceNumber (<externalId> and <orderItemReferenceNumber> elements)
                has_oir_Number = element.xpath(".//a:externalID[not(parent::a:dominantOrderItem) and a:key[normalize-space() != '']]" 
                                    + " | .//a:orderItemReferenceNumber[normalize-space() != '']", namespaces = self.nsmap)
                ref_for_oi = element.xpath("a:orderItemReferenceNumber[normalize-space() != '']", namespaces = self.nsmap)
                
                if len(ref_for_oi):
                    old_oi_ref = ref_for_oi[0].text
                    new_oi_ref = str(self.numberGen(len(old_oi_ref) - 1)) + "A"
                    
                    for node in has_oir_Number:
                        tag_name = etree.QName(node).localname
                        if tag_name == "externalID":
                            # Key should not be empty due to our xpath query above so below should never throw an error
                            key = node.xpath("./a:key", namespaces = self.nsmap)
                            print(f"Old Ref #: {key[0].text}")
                            key[0].text = new_oi_ref

                        else:
                            print(f"Old Ref #: {node.text}")
                            node.text = new_oi_ref  

                        print(f"New Ref #: {new_oi_ref}\n")

                    old_OIRefs[str(old_oi_ref)] = element # Save the changed order items for use with dominant order items

                else:
                    print("ERROR, Could not find order item reference number for the current order item, check order xml formatting.")
    
        def dominantOrderItemReplace(self, matches):
            # Need to get Associated OA IDs and change those and 
            associated_ids = self.root.xpath("//a:RBTCharacteristics[a:name[text()='Associated_OA_ID'] and a:value[normalize-space() != '']]", namespaces = self.nsmap)
            dominant_id_keys = self.root.xpath("//a:dominantOrderItem/a:externalID/a:key", namespaces = self.nsmap)
            # print(dominant_id_keys)
            # print(matches)
            if len(associated_ids):
                for element in associated_ids:
                    value = element.xpath("./a:value", namespaces = self.nsmap)[0] # Will never be empty because of above query
                    if value.text in matches:
                        replacement_ref = matches[value.text].xpath("a:orderItemReferenceNumber[normalize-space() != '']", namespaces = self.nsmap)
                        if len(replacement_ref):
                            print(f"Associated_OA_ID Value before {value.text}")
                            value.text = replacement_ref[0].text
                            print(f"Associated_OA_ID Value After: {value.text}")

                if len(dominant_id_keys):
                    for element in dominant_id_keys:
                        if element.text in matches:
                            replacement_ref = matches[element.text].xpath("a:orderItemReferenceNumber[normalize-space() != '']", namespaces = self.nsmap)
                            if len(replacement_ref):
                                print(f"dominantOrderItem Key Value before {element.text}")
                                element.text = replacement_ref[0].text
                                print(f"dominantOrderItem Key Value After: {element.text}")

            else:
                print("Order XML Has no Associated OA Ids")

        dominantOrderItemReplace(self, old_OIRefs)

    def replaceAll(self):
        self.orderIdReplace()
        self.samkeyReplace()
        self.cbpReplace()
        self.workIdReplace()
        self.hhidReplace()
        self.serialAndMacReplace()
        self.affectedProductReplace()
        self.orderItemIdReplace()
        print("\nSuccess!!")

def main():

    root = etree.parse("big_order_test.xml")
    nsmap={'x': 'http://www.w3.org/2001/XMLSchema-instance', 'ng': 'http://ngpp.fulfilment.services.rogers.com', 'a': 'http://fulfilment.services.cust.oms.amdocs.com'}
    order = createOrder(root, nsmap)

    with open("diy_child_new.xml", 'wb') as file:
        order.replaceAll()
        file.write(etree.tostring(order.root))
        # order.dominantOrderItemReplace()
        
        # for element in order.orderItemIdReplace():
        #     file.write(etree.tostring(element))
            

main()