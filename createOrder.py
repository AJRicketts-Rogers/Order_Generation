from lxml import etree
from random import randint, choice
import string, requests, datetime, base64, time, copy, logging

class createOrder:
    def __init__(self, root, nsmap, url, user, password, logger):
        self.root = root
        self.nsmap = nsmap
        self.url = url
        self.access_token = ''
        self.reference_number = ''
        self.batch = 1
        self.response = None
        self.logger = logger
        self.dispatcher = {"Provide": self.provide, "Change-Owner": self.changeOwner, "Cease": self.cease, "Move (All)": self.moveAll, "Move (Select)": self.moveSelect}

    def submitOrder(self, url, user = 'admin', password = 'welcome1'):

        authStr = base64.b64encode((user + ':' + password).encode('ascii'))
        headers = {'Authorization': 'Basic ' + authStr.decode('ascii'), 'Content-Type': 'application/soap+xml'}
        
        body = f"""
                <soapenv:Envelope xmlns:techord="http://xmlns.oracle.com/EnterpriseObjects/Core/EBO/TechnicalOrder/V1" xmlns:corecom="http://xmlns.oracle.com/EnterpriseObjects/Core/Common/V2" xmlns:ebo="http://xmlns.oracle.com/EnterpriseObjects/Core/EBO/TechnicalOrder/V1" xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd" xmlns:ws="http://xmlns.oracle.com/communications/ordermanagement" xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
                    <soapenv:Header>
                        <wsse:Security>
                            <wsse:UsernameToken>
                                <wsse:Username>{user}</wsse:Username>
                                <wsse:Password Type="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordText">{password}</wsse:Password>
                            </wsse:UsernameToken>
                        </wsse:Security>
                    </soapenv:Header>
                    <soapenv:Body>
                        <ws:CreateOrder>
                            {etree.tostring(self.root, encoding='unicode')}
                        </ws:CreateOrder>
                    </soapenv:Body>
                </soapenv:Envelope>
        """

        try:
            self.logger.info("Attempting to submit the order.....\n")
            response = requests.post(url,data=body,headers=headers)
            self.response = response
            self.logger.debug(response.text)
            content_type = response.headers.get('Content-Type', '')

        except requests.exceptions.RequestException as e:
            self.logger.error("\nError:")
            raise SystemExit(e)
        
        else:
            response_map = {'env': 'http://schemas.xmlsoap.org/soap/envelope/', 'n1': 'http://xmlns.oracle.com/communications/ordermanagement'}
            failed = False

            if 'Fault' in response.text or 'text/html' in content_type:
                failed = True
            else:
                success_response_reference = etree.fromstring(response.text).xpath("//env:Envelope/env:Body//n1:Reference", namespaces = response_map)
                success_order_id = etree.fromstring(response.text).xpath("//env:Envelope/env:Body//n1:Id", namespaces = response_map)
                success_order_type = etree.fromstring(response.text).xpath("//env:Envelope/env:Body//n1:Type", namespaces = response_map)
                success_version_number = etree.fromstring(response.text).xpath("//env:Envelope/env:Body//n1:Version", namespaces = response_map)

                if success_response_reference and success_order_id and success_order_type and success_version_number:
                    self.reference_number = success_response_reference[0].text
                    self.logger.info(f"Order Submitted!\nReference Number: {self.reference_number}\n\n")
                    self.logger.debug(f"{success_order_type[0].text} order id: {success_order_id[0].text}\n")
                    self.logger.info(f"Cartridge Version Number: {success_version_number[0].text}\n")
                
                else:
                    failed = True

            if failed:
                self.logger.error("\tError submitting order and getting order information, check response output. ---->\n")
                self.reference_number = "Error"
                
                if 'text/html' in content_type:
                    self.logger.info(response.text)
                else:
                    self.prettyprint(response.text)


    def getOutputFilename(self):
        curTime = datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S%f')
        return f'order_{curTime}' # Change filename here.

    def prettyprint(self, elements, **kwargs):
        if isinstance(elements, str):
        #     print("here")
            element = etree.fromstring(elements)
            xml = etree.tostring(element, pretty_print=True, **kwargs)
            print(xml.decode(), end='')
        
        else:
            for element in elements:
                xml = etree.tostring(element, pretty_print=True, **kwargs)
                print(xml.decode(), end='')

        print("\n\n")

    def numberGen(self, n) -> int:
        range_start = 10 ** (n-1) 
        range_end = (10 ** n) - 1

        return randint(range_start, range_end)

    def id_generator(self, size, chars = string.ascii_uppercase + string.digits, isMac = False):
        # Check the requirements for serial number and mac address formatting
        # Use Hexadecimal ONLY
        if isMac:
            valid = "ABCDEF123456789"
            return ''.join(choice(valid) for _ in range(12))
        else:
            return ''.join(choice(chars) for _ in range(size))

    def replace(self, elements, length, elementName) -> None:

        # Look at the first elements text, check if the first character is numeric (is a number), if so True, else False
        ishhid = False if elements[0].text[:1].isnumeric() else True
        count = 0

        self.logger.debug(f"Old {elementName} value: {elements[0].text}")
        if ishhid:
            cbp = self.getCBP()
            length -= len(cbp)
            # print("Length: ", length)
            new_value = self.numberGen(length)
            for element in elements:
                element.text = element.text[:1] + cbp + str(new_value) # Keep the letter (first character of the hhid) and replace all numbers after
                count += 1
        else:
            # print("Length: ", length)
            new_value = self.numberGen(length)
            for element in elements:
                element.text = str(new_value)
                count += 1

        self.logger.debug(f"New {elementName} value: {elements[0].text}")

        self.logger.debug("\tNumber of values changed: %s", count)
        self.logger.debug("\n")
        
    def getCBP(self):
        return self.root.xpath("//a:customer/a:Id[text()]", namespaces = self.nsmap)[0].text

    def orderIdReplace(self):
        # CHECK IF THE ORDER ID'S WILL EVER BE IN ANOTHER PLACE

        rbt_characteristics = self.root.xpath("//a:ProductOrder/a:orderItems/a:RBTCharacteristics[a:name[text()='OrderID'] and a:value[normalize-space() != '']]", namespaces = self.nsmap)
        if len(rbt_characteristics):
            old_orderId_element = rbt_characteristics[0].xpath("./a:value", namespaces = self.nsmap)
            old_orderId = old_orderId_element[0].text

            order_ids = self.retrieveValues(rbt_characteristics)

            self.replace(order_ids, len(old_orderId), "OrderID")
        
        
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
            self.replace(samkeys, len(samkeys[0].text), "SamKey")


    def cbpReplace(self) -> None:
        # Will this always only be in the customer elements
        # Do I need to change the registration key? As part of it is built with the CBP
        cbp_parent = self.root.xpath("//a:customer/a:Id[text()]", namespaces = self.nsmap)

        if len(cbp_parent):
            old_cbp = cbp_parent[0].text
            self.replace(cbp_parent, len(old_cbp), "CBP")
        

    def workIdReplace(self) -> None:
        workId_parent = self.root.xpath("//a:RBTCharacteristics[a:name[text()='WorkOrderId'] and a:value[normalize-space() != '']]", namespaces = self.nsmap)
        if len(workId_parent):
            workIds = self.retrieveValues(workId_parent)
            old_workId = workIds[0].text
            self.replace(workIds, len(old_workId), "WorkOrderId")

    def hhidReplace(self) -> None:
        # Always call after cbp has already been replaced with new value
        hhid_parent = self.root.xpath("//a:RBTCharacteristics[a:name[text()='HHID'] and a:value[normalize-space() != '']]", namespaces = self.nsmap)
        if len(hhid_parent):
            hhids = self.retrieveValues(hhid_parent)
            old_hhid = hhids[0].text
            self.replace(hhids, len(old_hhid) - 1, "HHID") # Subtract 1 from the length for letter at the beginning

    def serialReplace(self) -> None:
        # Do I need to change all these mac addresses?
        serial_parent = self.root.xpath("//a:characteristicValues[a:name[text()='Serial_Number'] and a:value[normalize-space() != '']]", namespaces = self.nsmap)
        count = 0

        self.logger.debug("========== Serial Number Replacement ==========\n")

        # self.prettyprint(serial_parent)
        if len(serial_parent):
            vals_to_change = []
            for element in serial_parent:
                vals_to_change.append(element.xpath("./a:name", namespaces = self.nsmap)[0].text)

            self.logger.debug(f"\tElement Values to Change: {vals_to_change}\n")

            serial_numbers = self.retrieveValues(serial_parent)

            for serial_number in serial_numbers:
                length = len(serial_number.text)
                # print("Old value: ", serial_number.text)
                serial_number.text = self.id_generator(length) # If the value is 'NA' replace?
                count += 1
                
            self.logger.debug("\tNew value: %s\n", serial_number.text)

            self.logger.debug(f"\tNumber of values changed: {count}\n")

    def macAddressReplace(self) -> None:
        mac_parent = self.root.xpath("//a:characteristicValues[a:name[contains(text(), ('MAC_Address')) or contains(text(), ('Mac_Address'))]" 
                                + " and a:value[normalize-space() != '']]", namespaces = self.nsmap)
        count = 0

        self.logger.debug("========== Mac Address Replacement ==========")

        if len(mac_parent):
            vals_to_change = []

            for element in mac_parent:
                vals_to_change.append(element.xpath("./a:name", namespaces = self.nsmap)[0].text)

            self.logger.debug(f"\tElement Values to Change: {vals_to_change}\n")

            mac_addresses = self.retrieveValues(mac_parent)

            for mac_address in mac_addresses:
                length = len(mac_address.text)
                # print("Old Mac value: ", mac_address.text)
                mac_address.text = self.id_generator(length, isMac=True) # If the value is 'NA' replace?
                count += 1
                
                self.logger.debug("\tNew Mac value: %s\n", mac_address.text)

            self.logger.debug(f"\tNumber of values changed: {count}\n")

    def affectedProductReplace(self, start_element) -> None:
        # TODO FUTURE FUNCTIONALITY Change all REF_AP's and roleRecievers as well
        # Do I need to replace roleReceiver as well?
        # What about REF_AP_ID??

        ap_parent = start_element.xpath(".//a:affectedProduct", namespaces = self.nsmap)
        self.logger.debug("========== Affected Product ID Replacement ==========\n")

        # Change both affected product id and APID value to the same number for each affectd product
        for element in ap_parent:
            id = element.xpath("./a:ID", namespaces = self.nsmap)
            ap_id = element.xpath("./a:characteristicValues[a:name[text()='APID']]", namespaces = self.nsmap)

            if len(id) and len(ap_id):
                new_id = self.numberGen(len(id[0].text))
                # self.logger.debug(f"Old Affected Product id: {id[0].text}")
                id[0].text = str(new_id)
                ap_id_value = self.retrieveValues(ap_id)[0]
                ap_id_value.text = str(new_id)
                # self.logger.debug(f"New Affected Product id: {new_id}\n")


    def orderItemIdReplace(self):
        self.logger.debug("========== Order Item Reference Number Replacement ==========")
        orderItems = self.root.xpath("//a:orderItems", namespaces = self.nsmap)
        old_OIRefs = {}
        if len(orderItems):
            for element in orderItems:
                # print("\nNew Order Item")
                
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
                            # self.logger.debug(f"Old Ref #: {key[0].text}")
                            key[0].text = new_oi_ref

                        else:
                            # self.logger.debug(f"Old Ref #: {node.text}")
                            node.text = new_oi_ref  

                        # self.logger.debug(f"New Ref #: {new_oi_ref}\n")

                    old_OIRefs[str(old_oi_ref)] = element # Save the changed order items for use with dominant order items

                else:
                    self.logger.error("\tERROR, Could not find order item reference number for the current order item, check order xml formatting.")
    
        def dominantOrderItemReplace(self, matches):
            associated_ids = self.root.xpath("//a:RBTCharacteristics[a:name[text()='Associated_OA_ID'] and a:value[normalize-space() != '']]", namespaces = self.nsmap)
            dominant_id_keys = self.root.xpath("//a:dominantOrderItem/a:externalID/a:key", namespaces = self.nsmap)

            if len(associated_ids):
                for element in associated_ids:
                    value = element.xpath("./a:value", namespaces = self.nsmap)[0] # Will never be empty because of above query
                    if value.text in matches:
                        replacement_ref = matches[value.text].xpath("a:orderItemReferenceNumber[normalize-space() != '']", namespaces = self.nsmap)
                        if len(replacement_ref):
                            self.logger.debug(f"Associated_OA_ID Value before {value.text}")
                            value.text = replacement_ref[0].text
                            self.logger.debug(f"Associated_OA_ID Value After: {value.text}")

                if len(dominant_id_keys):
                    for element in dominant_id_keys:
                        if element.text in matches:
                            replacement_ref = matches[element.text].xpath("a:orderItemReferenceNumber[normalize-space() != '']", namespaces = self.nsmap)
                            if len(replacement_ref):
                                self.logger.debug(f"dominantOrderItem Key Value before {element.text}")
                                element.text = replacement_ref[0].text
                                self.logger.debug(f"dominantOrderItem Key Value After: {element.text}")

            else:
                self.logger.error("\tOrder XML Has no Associated OA Ids")

        dominantOrderItemReplace(self, old_OIRefs)

    def provide(self):
            self.changeOrderType(self.root, action = "PR", type = "PR")
            self.replaceAll()

    def changeOwner(self):
            self.changeOrderType(self.root, action = "CH", type = "CW") 
            self.orderIdReplace()
            self.cbpReplace()

    def cease(self):
        self.changeOrderType(self.root, action = "CE", type = "CE")
        self.orderIdReplace()
        self.cbpReplace()

    def moveAll(self):
        self.logger.debug("========== Move Scenario ==========\n")
        self.changeOrderType(self.root, action = "CM", type = "CM")
        order_items = self.root.xpath("//a:ProductOrder/a:orderItems", namespaces = self.nsmap)

        for element in order_items:
            new_element = copy.deepcopy(element)
            self.changeOrderType(new_element, action="PV", type="PV")
            self.affectedProductReplace(new_element)
            element.addnext(new_element)
        
    
    def moveSelect(self):
        self.changeOrderType(self.root, action = "CM", type = "CM")

        self.logger.debug("========== Move Scenario ==========\n")
        
        order_items = self.root.xpath("//a:ProductOrder/a:orderItems", namespaces = self.nsmap)
        line_item_elements = {}
        line_item_names = {}
        index = 0

        for element in order_items:
            ap_parent = element.xpath(".//a:affectedProduct/a:productSpec/a:code | .//affectedProduct/a:children/a:affectedProduct/a:productSpec/a:code", namespaces = self.nsmap)

            if len(ap_parent):
                for elem in ap_parent:
                    line_item_elements[elem.text] = elem
                    line_item_names[index] = elem.text
                    index += 1

        # Modified menu()
        time.sleep(0.4)
        print("\n==================================================")
        for index in line_item_names.keys():
            print(f"[{index + 1}] {line_item_names[index]}")

        exit_message = "[0] Back\n"
        print(exit_message)

        print("Which line items would you like to include in the move?")
        message = "For all, leave blank. For specific items type each item number with a space i.e 1 2 3"
        items_to_move = ensureValidChoiceMultiple(message, len(line_item_names))
        selection = []

        if items_to_move == "":
            for element in line_item_elements.values():
                selection = element
        elif 0 in items_to_move:
            self.logger.debug("\tthey want to go back")
        else:
            for index in items_to_move:
                # line_items_elements is a key value pair of line item names (strings) as keys and <Element> objects as values
                # line_item_names is a key value pair of indexes (The numbers shown to the user) as keys and line item names (strings as values)
                # This will use the index the user selected to find the correct line item names and use that name to find the correct element
                selection.append(line_item_names[index])
        
        # print(selection)
        # Change both affected product id and APID value to the same number for each affectd product
        for name in selection:
            xpath_string = f"//a:affectedProduct[a:productSpec/a:code[text()='{name}']]"
            self.logger.debug(xpath_string)
            affected_product = self.root.xpath(xpath_string, namespaces = self.nsmap)
            if len(affected_product):
                parent = affected_product[0].xpath("..", namespaces = self.nsmap)

                id = affected_product[0].xpath("./a:ID", namespaces = self.nsmap)
                ap_id = affected_product[0].xpath("./a:characteristicValues[a:name[text()='APID']]", namespaces = self.nsmap)
                action = affected_product[0].xpath(".//")

                if len(id) and len(ap_id):
                    new_id = self.numberGen(len(id[0].text))
                    self.logger.debug(f"Old Affected Product id: {id[0].text}")
                    
                    id[0].text = str(new_id)
                    ap_id_value = self.retrieveValues(ap_id)[0]
                    ap_id_value.text = str(new_id)
                    
                    self.logger.debug(f"New Affected Product id: {new_id}\n")

    
    def changeActionCodes(self, element, action:string):
        action_codes = element.xpath(".//a:action/a:code", namespaces = self.nsmap)
        actions = set()
        if len(action_codes):
            oldAction = action_codes[0].text
            
            for element in action_codes:
                actions.add(element.text)
                element.text = action

            self.logger.debug(f"Action Codes changed from {actions} to {action_codes[0].text}")

    def changeTypeCodes(self, element, type:string):
        type_codes = element.xpath(".//a:type/a:code", namespaces = self.nsmap)
        if len(type_codes):
            oldTypes = type_codes[0].text

            for element in type_codes:
                element.text = type
            self.logger.debug(f"Type Codes changed from {oldTypes} to {type_codes[0].text}")

    def changeOrderType(self, element, action : string, type : string):
        self.changeActionCodes(element, action)
        self.changeTypeCodes(element, type)

    def replaceAll(self):
        self.orderIdReplace()
        self.samkeyReplace()
        self.cbpReplace()
        self.workIdReplace()
        self.hhidReplace()
        self.serialReplace()
        self.macAddressReplace()
        self.affectedProductReplace(self.root)
        self.orderItemIdReplace()
        self.logger.debug("Values Replaced!\n")


def ensureValidChoiceMultiple(message, acceptRange) -> int:
    while True:
        try:
            print(message)
            print("==================================================")
            userInput = input(">> ")
            if userInput == "":
                return ""
            
            vals = userInput.split()
            ret = []
            for val in vals:
                ret.append(int(val))
            # val = int(userInput)

        except ValueError:
            print("\nNot a number")
        
        else:
            for index, val in enumerate(ret):
                if val in range(acceptRange + 1):
                    if index == len(ret) - 1:
                        return ret
                    else:
                        continue
                else:
                    print("Not a valid choice!")
                    break