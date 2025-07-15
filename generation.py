from lxml import etree
from random import randint, choice
import string, requests, sys, datetime, os, base64, time, copy

class createOrder:
    def __init__(self, root, nsmap, url, user, password):
        self.root = root
        self.nsmap = nsmap
        self.url = url
        self.access_token = ''
        self.dispatcher = {"Provide": self.replaceAll, "Change-Owner": self.changeOwner, "Cease": self.cease, "Move (All)": self.moveAll, "Move (Select)": self.moveSelect}

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
            print("\nAttempting to submit the order.....")
            response = requests.post(url,data=body,headers=headers)

        except requests.exceptions.RequestException as e:
            print("\nError:")
            raise SystemExit(e)
        
        else:
            response_map = {'env': 'http://schemas.xmlsoap.org/soap/envelope/', 'n1': 'http://xmlns.oracle.com/communications/ordermanagement'}
            
            success_response_reference = etree.fromstring(response.text).xpath("//env:Envelope/env:Body//n1:Reference", namespaces = response_map)
            success_order_id = etree.fromstring(response.text).xpath("//env:Envelope/env:Body//n1:Id", namespaces = response_map)
            success_order_type = etree.fromstring(response.text).xpath("//env:Envelope/env:Body//n1:Type", namespaces = response_map)

            if success_response_reference and success_order_id and success_order_type:
                print(f"\n\nOrder Submitted!\nReference Number: {success_response_reference[0].text}")
                print(f"\n{success_order_type[0].text} order id: {success_order_id[0].text}")

            else:
                print("Error submitting order and getting order information, check response output. ---->\n")
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

        print(f"Old {elementName} value: {elements[0].text}")
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

        # print(f"New {elementName} value: {elements[0].text}")
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

        print("========== Serial Number Replacement ==========")

        # self.prettyprint(serial_parent)
        if len(serial_parent):
            vals_to_change = []
            for element in serial_parent:
                vals_to_change.append(element.xpath("./a:name", namespaces = self.nsmap)[0].text)

            print(f"Element Values to Change: {vals_to_change}\n")

            serial_numbers = self.retrieveValues(serial_parent)

            for serial_number in serial_numbers:
                length = len(serial_number.text)
                # print("Old value: ", serial_number.text)
                serial_number.text = self.id_generator(length) # If the value is 'NA' replace?
                count += 1
                
                # print("New value: ", serial_number.text)

            print(f"Number of values changed: {count}\n")

    def macAddressReplace(self) -> None:
        mac_parent = self.root.xpath("//a:characteristicValues[a:name[contains(text(), ('MAC_Address')) or contains(text(), ('Mac_Address'))]" 
                                + " and a:value[normalize-space() != '']]", namespaces = self.nsmap)
        count = 0

        print("========== Mac Address Replacement ==========")

        if len(mac_parent):
            vals_to_change = []

            for element in mac_parent:
                vals_to_change.append(element.xpath("./a:name", namespaces = self.nsmap)[0].text)

            print(f"Element Values to Change: {vals_to_change}\n")

            mac_addresses = self.retrieveValues(mac_parent)

            for mac_address in mac_addresses:
                length = len(mac_address.text)
                # print("Old Mac value: ", mac_address.text)
                mac_address.text = self.id_generator(length, isMac=True) # If the value is 'NA' replace?
                count += 1
                
                # print("New Mac value: ", mac_address.text)

            print(f"Number of values changed: {count}\n")

    def affectedProductReplace(self, start_element) -> None:
        # TODO FUTURE FUNCTIONALITY Change all REF_AP's and roleRecievers as well
        # Do I need to replace roleReceiver as well?
        # What about REF_AP_ID??

        ap_parent = start_element.xpath(".//a:affectedProduct", namespaces = self.nsmap)
        print("========== Affected Product ID Replacement ==========\n")

        # Change both affected product id and APID value to the same number for each affectd product
        for element in ap_parent:
            id = element.xpath("./a:ID", namespaces = self.nsmap)
            ap_id = element.xpath("./a:characteristicValues[a:name[text()='APID']]", namespaces = self.nsmap)

            if len(id) and len(ap_id):
                new_id = self.numberGen(len(id[0].text))
                # print(f"Old Affected Product id: {id[0].text}")
                id[0].text = str(new_id)
                ap_id_value = self.retrieveValues(ap_id)[0]
                ap_id_value.text = str(new_id)
                # print(f"New Affected Product id: {new_id}\n")


    def orderItemIdReplace(self):
        # TODO Figure out the correct format for reference numbers (9 Numbers and then a Letter?)
        print("========== Order Item Reference Number Replacement ==========")
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
                            # print(f"Old Ref #: {key[0].text}")
                            key[0].text = new_oi_ref

                        else:
                            # print(f"Old Ref #: {node.text}")
                            node.text = new_oi_ref  

                        # print(f"New Ref #: {new_oi_ref}\n")

                    old_OIRefs[str(old_oi_ref)] = element # Save the changed order items for use with dominant order items

                else:
                    print("ERROR, Could not find order item reference number for the current order item, check order xml formatting.")
    
        def dominantOrderItemReplace(self, matches):
            associated_ids = self.root.xpath("//a:RBTCharacteristics[a:name[text()='Associated_OA_ID'] and a:value[normalize-space() != '']]", namespaces = self.nsmap)
            dominant_id_keys = self.root.xpath("//a:dominantOrderItem/a:externalID/a:key", namespaces = self.nsmap)

            if len(associated_ids):
                for element in associated_ids:
                    value = element.xpath("./a:value", namespaces = self.nsmap)[0] # Will never be empty because of above query
                    if value.text in matches:
                        replacement_ref = matches[value.text].xpath("a:orderItemReferenceNumber[normalize-space() != '']", namespaces = self.nsmap)
                        if len(replacement_ref):
                            # print(f"Associated_OA_ID Value before {value.text}")
                            value.text = replacement_ref[0].text
                            # print(f"Associated_OA_ID Value After: {value.text}")

                if len(dominant_id_keys):
                    for element in dominant_id_keys:
                        if element.text in matches:
                            replacement_ref = matches[element.text].xpath("a:orderItemReferenceNumber[normalize-space() != '']", namespaces = self.nsmap)
                            if len(replacement_ref):
                                # print(f"dominantOrderItem Key Value before {element.text}")
                                element.text = replacement_ref[0].text
                                # print(f"dominantOrderItem Key Value After: {element.text}")

            else:
                print("Order XML Has no Associated OA Ids")

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
        print("========== Move Scenario ==========\n")
        self.changeOrderType(self.root, action = "CM", type = "CM")
        order_items = self.root.xpath("//a:ProductOrder/a:orderItems", namespaces = self.nsmap)

        for element in order_items:
            new_element = copy.deepcopy(element)
            self.changeOrderType(new_element, action="PV", type="PV")
            self.affectedProductReplace(new_element)
            element.addnext(new_element)
        
    
    def moveSelect(self):
        self.changeOrderType(self.root, action = "CM", type = "CM")

        order_items = self.root.xpath("//a:ProductOrder/a:orderItems", namespaces = self.nsmap)
        print("========== Move Scenario ==========\n")
        # print(order_items)
        line_item_elements = {}
        line_item_names = {}
        index = 0
        for element in order_items:
            ap_parent = element.xpath(".//a:affectedProduct/a:productSpec/a:code | .//affectedProduct/a:children/a:affectedProduct/a:productSpec/a:code", namespaces = self.nsmap)
            # print(ap_parent)
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
            print("they want to go back")
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
            print(xpath_string)
            affected_product = self.root.xpath(xpath_string, namespaces = self.nsmap)
            if len(affected_product):
                parent = affected_product[0].xpath("..", namespaces = self.nsmap)

                id = affected_product[0].xpath("./a:ID", namespaces = self.nsmap)
                ap_id = affected_product[0].xpath("./a:characteristicValues[a:name[text()='APID']]", namespaces = self.nsmap)
                action = affected_product[0].xpath(".//")

                if len(id) and len(ap_id):
                    new_id = self.numberGen(len(id[0].text))
                    # print(f"Old Affected Product id: {id[0].text}")
                    id[0].text = str(new_id)
                    ap_id_value = self.retrieveValues(ap_id)[0]
                    ap_id_value.text = str(new_id)
                    # print(f"New Affected Product id: {new_id}\n")

    
    def changeActionCodes(self, element, action:string):
        action_codes = element.xpath(".//a:action/a:code", namespaces = self.nsmap)
        actions = set()
        if len(action_codes):
            oldAction = action_codes[0].text
            
            for element in action_codes:
                actions.add(element.text)
                print(element.text)
                element.text = action
            # print(f"Action Codes changed from {actions} to {action_codes[0].text}")

    def changeTypeCodes(self, element, type:string):
        type_codes = element.xpath(".//a:type/a:code", namespaces = self.nsmap)
        if len(type_codes):
            oldTypes = type_codes[0].text

            for element in type_codes:
                element.text = type
            # print(f"Type Codes changed from {oldTypes} to {type_codes[0].text}")

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
        # self.provide()
        print("\nValues Replaced!")

def writeToFile(outputFn, order: createOrder):
        
    with open("%s.xml" % outputFn, 'wb') as file:
        print(f"\nOutput Filename: {outputFn}.xml")
        file.write(etree.tostring(order.root))

def outputFileRun(credentials, orderType, outputFn = ''):
    fp = credentials[0]
    nsmap = credentials[1]
    url = credentials[2]
    user = credentials[3]
    password = credentials[4]
        
    try:
        root = etree.parse(fp)
    except:
        print("Error parsing file. Check filename")
        return
    else:

        order = createOrder(root, nsmap, url, user, password)
    
        if len(outputFn) == 0:
            outputFn = order.getOutputFilename() + "_" + "Provide"

        # Create provide order
        order.replaceAll()
        writeToFile(outputFn, order)
        
        if orderType != "Provide":
            outputFn = order.getOutputFilename() + "_" + orderType
            # Create second order
            order.dispatcher[orderType]()
            
            writeToFile(outputFn, order)
            with open("%s.xml" % outputFn, 'wb') as file:
                print(f"\nOutput Filename: {outputFn}.xml")
                file.write(etree.tostring(order.root))


def submitRun(credentials) -> createOrder:
    fp = credentials[0]
    nsmap = credentials[1]
    url = credentials[2]
    user = credentials[3]
    password = credentials[4]
    
        
    try:
        root = etree.parse(fp)
    except:
        print("Error parsing file. Check filename")
        return
    else:
        order = createOrder(root, nsmap, url, user, password)
        order.provide()
        order.submitOrder(url)

    return order

def menu(options, firstCall = False):
    
    time.sleep(0.4)
    print("\n==================================================")
    for index, option in enumerate(options, start=1):
        print(f"[{index}] {option}")

    exit_message = "[0] Exit" if firstCall else "[0] Back"
    print(exit_message)

def ensureValidChoice(message, acceptRange) -> int:
    while True:
        try:
            print(message)
            print("==================================================")
            userInput = input(">> ")
            val = int(userInput)

        except ValueError:
            print("\nNot a number")
        
        else:
            if val in range(acceptRange + 1):
                return val
            else:
                print("Not a valid choice!")

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


def chooseEnv() -> string:
    url = ""
    # Get Desired Dev or QA Environment
    envs = [("DEV 1", "http://osmdev1.ngpp.mgmt.vf.rogers.com:7001/OrderManagement/wsapi"), 
            ("DEV 4", "http://osmdev4.ngpp.mgmt.vf.rogers.com:7001/OrderManagement/wsapi"), 
            ("DEV 5", "http://osmdev5.ngpp.mgmt.vf.rogers.com:7001/OrderManagement/wsapi"), 
            ("QA 1", "http://osmqa1.ngpp.mgmt.vf.rogers.com:7001/OrderManagement/wsapi"), 
            ("QA 4", "http://osmqa4.ngpp.mgmt.vf.rogers.com:7001/OrderManagement/wsapi"), 
            ("QA 5", "http://osmqa5.ngpp.mgmt.vf.rogers.com:7001/OrderManagement/wsapi")]
    
    menu([e[0] for e in envs], firstCall=True)
    env = ensureValidChoice("Select Desired Environment: ", len(envs))
    if env == 0:
        return -1
    else:
        url = envs[env - 1][1]
    
    print(f"Setting Endpoint to: {url}")
    return url


def options():

    nsmap={'x': 'http://www.w3.org/2001/XMLSchema-instance', 'ng': 'http://ngpp.fulfilment.services.rogers.com', 'a': 'http://fulfilment.services.cust.oms.amdocs.com'}
    url = ""
    user = "admin"
    password = "welcome1"
    types = {1: "Provide", 2: "Change-Owner", 3: "Cease", 4: "Move (All)", 5: "Move (Select)"}

    if len(sys.argv) > 1:
        fp = sys.argv[1]
        print(f"\nFile Path: {fp}")
    else:
       print("Please provide a valid filename as a command line argument (Ex. py generation.py order.xml)")
       return
    
    # Set credentials
    credentials = [fp, nsmap, url, user, password]


    ############ MENU ############
    
    # TODO CLEAN ALL OF THIS UP
    menu(["Replace All", "Replace Specific Values", "Submit Order"], firstCall=True)
    option = ensureValidChoice("Specific Value Change or Whole Order?: ", 3)
    if option == 0:
        return
    elif option == 2:
        individualFunctions(credentials)
        return
    elif option == 3:
        url = chooseEnv()
        if url == -1:
            return
        else:
            credentials[2] = url
            try:
                root = etree.parse(fp)
            except:
                print("Error parsing file. Check filename")
                return
            else:
                order = createOrder(root, nsmap, url, user, password)
                order.submitOrder(url)
                return

    url = chooseEnv()
    if url == "" or None:
        print("Error choosing environment")
    elif url == -1:
        return
    credentials[2] = url # Replace URL


    choices = ["OMS", "TOM"]
    menu(choices, firstCall=True)
    pick = ensureValidChoice("Which kind of order did you input?: ", len(choices))

    while pick != 0:

        # User picked OMS order (E2E)
        if pick == 1:
        
            choices = ["Singular", "Multiple"]
            menu(choices)
            pick = ensureValidChoice("Singular or Multiple Orders?: ", len(choices))

            if pick == 1:
                choices = ["Provide", "Change-Owneer", "Cease", "Move (All)", "Move (Select)"]
                menu(choices)
                orderTypeChoice = ensureValidChoice("What type of order?: ", len(choices))
                orderType = types[orderTypeChoice]

                choices = ["Output File(s)", "Submit"]
                menu(choices)
                ans = ensureValidChoice("Produce output file or submit the order?: ", len(choices))

                if ans == 1:
                    filename = str(input("Enter Output Filename (Leave blank for generated filename or 0 to exit): "))
                    if filename == "0":
                        continue

                    outputFileRun(credentials, orderType, filename)
                    break

                elif ans == 2:
                    order: createOrder = submitRun(credentials)
                    if orderType != "Provide":
                        print("\n==================================================")
                        print("Secondary order will be written to file")
                        outputFn = order.getOutputFilename()
                        order.dispatcher[orderType]()
                        writeToFile(outputFn, order)
                    break

            elif pick == 2:
                try: 
                    numOrders = int(input("Number of orders?: "))
                except ValueError:
                    print("Not a number")
                else:

                    choices = ["Provide", "Change-Owneer", "Cease", "Move (All)", "Move (Select)"]
                    menu(choices)
                    orderTypeChoice = ensureValidChoice("What type of order?: ", len(choices))
                    orderType = types[orderTypeChoice]

                    choices = ["Output File(s)", "Submit"]
                    menu(choices)
                    ans = ensureValidChoice("Produce output file or submit the order?: ", len(choices))

                    if ans == 1:
                        filename = str(input("Enter Output Filename (Leave blank for generated filename or 0 to exit): "))
                        if filename == "0":
                            continue
                        
                        for _ in range(numOrders):
                            outputFileRun(credentials, orderType, filename)
                        break

                    elif ans == 2:
                        for _ in range(numOrders):
                            order: createOrder = submitRun(credentials)
                        break
        
        # User picked TOM
        else:
            choices = ["Singular", "Multiple"]
            menu(choices)
            pick = ensureValidChoice("Singular or Multiple Orders?: ", len(choices))

            if pick == 1:
                choices = ["Output File(s)", "Submit"]
                menu(choices)
                ans = ensureValidChoice("Produce output file or submit the order?: ", len(choices))

                if ans == 1:
                    filename = str(input("Enter Output Filename (Leave blank for generated filename or 0 to exit): "))
                    if filename == "0":
                        continue

                    outputFileRun(credentials, orderType, filename)
                    break

                elif ans == 2:
                    order: createOrder = submitRun(credentials)
                    break

            elif pick == 2:
                try: 
                    numOrders = int(input("Number of orders?: "))
                except ValueError:
                    print("Not a number")
                else:
                    
                    for i in range(numOrders):
                        outputFileRun(credentials)
                    break


        choices = ["OMS", "TOM"]
        menu(choices, firstCall=True)
        pick = ensureValidChoice("Which kind of order did you input?: ", len(choices))
    
    return                


def individualFunctions(credentials:list):
    fp = credentials[0]
    nsmap = credentials[1]
    url = credentials[2]
    user = credentials[3]
    password = credentials[4]
    
    try:
        root = etree.parse(fp)
    except:
        print("Error parsing file. Check filename")
        return
    else:
        order = createOrder(root, nsmap, url, user, password)
        dispatcher = {1: order.orderIdReplace, 2: order.samkeyReplace, 3: order.cbpReplace, 4: order.workIdReplace, 
                      5: order.hhidReplace, 6: order.serialReplace, 7: order.macAddressReplace, 8: order.orderItemIdReplace}

        while True:
            choices = {1: "Order ID (Reference #)", 
                       2: "Samkey", 
                       3: "CBP", 
                       4: "Work Order ID", 
                       5: "HHID", 
                       6: "Serial Number", 
                       7: "Mac Address", 
                       8: "Order Item IDs", 
                       9: "Action Codes", 
                       10: "Type Codes",
                       11: "Product Instance IDs", 
                       12: "Submit Order"}
            

            menu(choices.values(), firstCall=True)
            pick = ensureValidChoice("What value would you like to replace?: ", len(choices))

            if pick == 0:
                break
            else:
                if pick >= 9:
                    if pick == 9:
                        print("Please provide the desired action code: ")
                        value = input(">> ")
                        order.changeActionCodes(order.root, value.capitalize())
                    elif pick == 10:
                        print("Please provide the desired type code: ")
                        value = input(">> ")
                        order.changeTypeCodes(order.root, value.capitalize())
                    elif pick == 11:
                        order.affectedProductReplace(root)
                    else:
                        # TODO FIX THIS
                        print("Are you done changing values? Are you sure you want to submit the order?: ")
                        value = input("Y or N? >> ")
                        if value.casefold() == "Y".casefold():
                            url = chooseEnv()
                            order.submitOrder(url)
                            return
                        else:
                            continue
                else:
                    dispatcher[pick]()

        outputfn = order.getOutputFilename()
        writeToFile(outputfn, order)
            
        return

def testing():

    if len(sys.argv) > 1:
        fp = sys.argv[1]
        print(f"\nFile Path: {fp}\n")
    else:
       print("Please provide a valid filename as a command line argument (Ex. py generation.py order.xml)")
       return

    root = etree.parse(fp)
    nsmap={'x': 'http://www.w3.org/2001/XMLSchema-instance', 'ng': 'http://ngpp.fulfilment.services.rogers.com', 'a': 'http://fulfilment.services.cust.oms.amdocs.com'}
    url = "http://osmdev1-z1.ngpp.mgmt.vf.rogers.com:7001/OrderManagement/wsapi"
    user = "admin"
    password = "welcome1"
    order = createOrder(root, nsmap, url, user, password)

    order.orderIdReplace()
    order.changeActionCodes(order.root, "PR")

    outputFn = order.getOutputFilename()

    with open("%s.xml" % outputFn, 'wb') as file:
        print(f"\nOutput Filename: {outputFn}.xml")
        file.write(etree.tostring(order.root))

# testing()
options()