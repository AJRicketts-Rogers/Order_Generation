from zoneinfo import ZoneInfo
from lxml import etree
from random import randint, choice
import string, sys, time, logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from createOrder import createOrder
from datetime import datetime, timedelta, timezone
from dateutil import parser

logger = logging.getLogger(__name__)

def writeToFile(outputFn, order: createOrder):
        
    with open("%s.xml" % outputFn, 'wb') as file:
        logger.info(f"Output Filename: {outputFn}.xml\n")
        file.write(etree.tostring(order.root))

def outputFileRun(credentials, orderType, outputFn = ''):
    root = credentials[0]
    nsmap = credentials[1]
    url = credentials[2]
    user = credentials[3]
    password = credentials[4]

    order = createOrder(root, nsmap, url, user, password, logger)

    if len(outputFn) == 0:
        outputFn = order.getOutputFilename() + "_"
        if orderType == "Provide":
            outputFn += "Provide"
        else:
            outputFn += "Generated"

    # Create provide order
    if orderType != '':
        order.dispatcher[orderType]()
    else:
        order.replaceAll()
    
    writeToFile(outputFn, order)
    
    if orderType != "Provide" and orderType != '':
        outputFn = order.getOutputFilename() + "_" + orderType
        # Create second order
        order.dispatcher[orderType]()
        
        writeToFile(outputFn, order)
        with open("%s.xml" % outputFn, 'wb') as file:
            logger.info(f"Output Filename: {outputFn}.xml\n")
            file.write(etree.tostring(order.root))


def submitRun(credentials, orderType) -> createOrder:
    root = credentials[0]
    nsmap = credentials[1]
    url = credentials[2]
    user = credentials[3]
    password = credentials[4]
    
    print("\n================================================== NEW ORDER ==================================================\n")
    order = createOrder(root, nsmap, url, user, password, logger)
    if orderType != '':
        order.dispatcher[orderType]()
    else:
        order.replaceAll()
    order.submitOrder(url, user, password)

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


def chooseEnv() -> string:
    url = ""
    # Get Desired Dev or QA Environment
    envs = [("DEV 1", "http://osmdev1.ngpp.mgmt.vf.rogers.com:7001/OrderManagement/wsapi"),
            ("DEV 2", "http://osmdev2.ngpp.mgmt.vf.rogers.com:7001/OrderManagement/wsapi"),
            ("DEV 3", "http://osmdev3.ngpp.mgmt.vf.rogers.com:7001/OrderManagement/wsapi"), 
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


def chooseOrderType(serverTest=False):
    types = {1: "Provide", 2: "Change-Owner", 3: "Cease", 4: "Move (All)", 5: "Move (Select)"}
    ans = -1

    menu(["Yes", "No"])
    changeType = ensureValidChoice("Change order Type?: ", 2)

    if changeType == 0:
        return [ans, -1]
    elif changeType == 1:
        choices = list(types.values())
        menu(choices)
        orderTypeChoice = ensureValidChoice("What type of order? (Select Provide, still need to fix): ", len(choices))
        if orderTypeChoice == 0:
            return [ans, -1] # Return -1 to signify the user wants to go back in the menu
        orderType = types[orderTypeChoice]
    else:
        ans = 1 # Set to 1 in case the run is a server test
        orderType = ""

    if not serverTest:
        choices = ["Output File(s)", "Submit"]
        menu(choices)
        ans = ensureValidChoice("Produce output file or submit the order?: ", len(choices))

    return [ans, orderType]

def dueDateReplace(root, nsmap) -> None:
    menu(["Yes", "No"])
    changeDueDates  = ensureValidChoice("Change Due Dates?: ", 2)
    if changeDueDates != 1:
        return

    dates = root.xpath("//a:orderItems/a:dueDate | //a:affectedProduct/a:effectiveDate | //a:orderItems/a:serviceRequiredDate", namespaces = nsmap)
    if len(dates):
        initial_date = dates[0]
        
        # ISO 8601 datetime string with timezone
        dt_str = initial_date.text

        # Parse into aware datetime object
        dt_obj = parser.isoparse(dt_str)

        # Ask user for new time
        logger.info(f"Current date in the XML = {dt_str}\n")
        while True:
            try:
                date_input = input("Enter your desired date time (in the above format): ")
                format_string = "%Y-%m-%dT%H:%M:%S.%f%z"
                new_date = parser.isoparse(date_input)
            except ValueError:
                logger.info("Error, please input a valid date time in the following format: YYYY-MM-DDTHR:MN:SC.000-04:00 ")
                continue
            else:
                
                fulfillment_options = root.xpath("//a:affectedProduct/a:characteristicValues[a:name[text()='Fulfillment_Options']]", namespaces = nsmap)
                now = datetime.now(ZoneInfo("America/New_York"))
                new_val = "Error"

                for option in fulfillment_options:
                    value = option.xpath("./a:value", namespaces = nsmap)
                    if new_date > now:
                        value[0].text = "NN"
                    else:
                        value[0].text = "IM"
                    
                    new_val = value[0].text
                
                logger.debug("\tFulfillment Options changed to: %s", new_val)

                new_dt_str = new_date.isoformat()

                for date in dates:
                    date.text = new_dt_str

                logger.debug("\tDue dates changed from %s to %s\n", dt_str, new_dt_str)
                break

def submitMultiple(credentials, numOrders, orderType):
    try: 
        t_minutes = 0
        if numOrders == 0:
            t_minutes = float(input("\nSubmit orders for a certain length of time? Enter the desired time in minutes: "))

        batches_input = int(input("\nSubmit orders in batches? Enter the number of orders per batch (Enter 0 to submit all orders consecutively): "))
        delay = int(input("\nDelay in between orders/batches? (In seconds, enter 0 for no delay): "))
    except ValueError:
        logger.error("Not a number")
    else:
        reference_numbers = []
        processes = []
        batches = batches_input if batches_input > 0 else None
        t_end = time.time() + 60 * t_minutes if t_minutes > 0 else None

        start = time.time()
        with ThreadPoolExecutor(max_workers = 5) as executor:
            logger.debug("IN THREADPOOL")
            
            while (t_end and time.time() < t_end) or numOrders > 0:
                logger.debug("CALLING SUBMIT!!!!!")
                processes.append(executor.submit(submitRun, credentials, orderType))
                if numOrders > 0:
                    numOrders -= 1

                if batches != None:
                    batches -= 1
                    if batches == 0:
                        batches = batches_input
                        logger.info(f"Delaying for {delay} seconds.....\n")
                        time.sleep(delay)

                elif delay:
                    logger.info(f"Starting new order in {delay} seconds.....\n")
                    time.sleep(delay)

                time.sleep(0.1)

        logger.debug(f"Processes = {processes}\n")
        for task in as_completed(processes):
            if task.result() != None:
                reference_numbers.append(task.result().reference_number)
            
        logger.info(f"Finished submitting orders in {time.time() - start}s")
        print(f"Submitted Reference Numbers: {reference_numbers}")
        return


def options(nsmap, user, password):

    if len(sys.argv) > 1:
        fp = sys.argv[1]
        logger.info(f"File Path: {fp}\n")
    else:
       logger.info("Please provide a valid filename as a command line argument (Ex. py generation.py order.xml)")
       return
    
    # Parse the XML
    root = None
    while not root:
        try:
            root = etree.parse(fp)
        except:
            logger.error("Error parsing file. Check filename")
    
    url = chooseEnv()
    if url == "" or None:
        logger.error("Error choosing environment")
        return
    elif url == -1:
        return

    # Set credentials
    credentials = [root, nsmap, url, user, password]


    ############ MENU ############

    # TODO Add change due date / serviceRequiredDate function

    menu(["Replace All", "Replace Specific Values", "Submit Order", "Server Load Test"], firstCall=True)
    option = ensureValidChoice("Specific Value Change or Whole Order?: ", 4)
    if option == 0:
        return
    elif option == 2:
        individualFunctions(credentials)
        return
    elif option == 3:
        dueDateReplace(root, nsmap)
        order = createOrder(root, nsmap, url, user, password, logger)
        order.submitOrder(url)
        return
            
    elif option == 4:
        dueDateReplace(root, nsmap)
        orderTypeAns = chooseOrderType(serverTest=True)
        ans = orderTypeAns[0]
        orderType = orderTypeAns[1]
        if ans == -1:
            return
        else:
            while True:
                try:
                    numOrders = int(input("Number of orders? (For order submission, enter 0 if a length of time is preffered): "))
                except ValueError:
                    logger.error("Not a number")
                else:
                    submitMultiple(credentials, numOrders, orderType)
                    break

    else:
        exit = False

        while exit != True:

            choices = ["OMS", "TOM"]
            menu(choices, firstCall=True)
            pick = ensureValidChoice("Which kind of order did you input?: ", len(choices))
            if pick == 0:
                exit = True 

            # User picked OMS order (E2E)
            if pick == 1:
            
                while True:
                    choices = ["Singular", "Multiple"]
                    menu(choices)
                    pick = ensureValidChoice("Singular or Multiple Orders?: ", len(choices))

                    if pick == 1:
                        while True:
                            dueDateReplace(root, nsmap)
                            orderTypeAns = chooseOrderType()
                            ans = orderTypeAns[0]
                            orderType = orderTypeAns[1]

                            if ans == 1:
                                filename = str(input("Enter Output Filename (Leave blank for generated filename or 0 to exit): "))
                                if filename == "0":
                                    break

                                outputFileRun(credentials, orderType, filename)
                                return

                            elif ans == 2:
                                order: createOrder = submitRun(credentials, orderType)
                                if orderType != "Provide" and orderType != "":
                                    print("\n==================================================")
                                    print("Secondary order will be written to file")
                                    outputFn = order.getOutputFilename()
                                    order.dispatcher[orderType]()
                                    writeToFile(outputFn, order)
                                
                                return
                            else:
                                break

                    elif pick == 2:
                        try: 
                            numOrders = int(input("Number of orders? (For order submission, enter 0 if a length of time is preffered): "))
                        except ValueError:
                            logger.error("Not a number")
                        else:

                            while True:
                                dueDateReplace(root, nsmap)
                                orderTypeAns = chooseOrderType()
                                ans = orderTypeAns[0]
                                orderType = orderTypeAns[1]

                                if ans == 1:
                                    filename = str(input("Enter Output Filename (Leave blank for generated filename or 0 to exit): "))
                                    if filename == "0":
                                        break
                                    
                                    for _ in range(numOrders):
                                        outputFileRun(credentials, orderType, filename)
                                    return

                                elif ans == 2:
                                    submitMultiple(credentials, numOrders, orderType)
                                    return
                                else:
                                    break
                    else:
                        break
                                    
            
            # User picked TOM
            if pick == 2:
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
                        exit = True
                        break

                    elif ans == 2:
                        order: createOrder = submitRun(credentials, orderType)
                        exit = True
                        break

                elif pick == 2:
                    try: 
                        numOrders = int(input("Number of orders?: "))
                    except ValueError:
                        logger.error("Not a number")
                    else:
                        
                        for i in range(numOrders):
                            outputFileRun(credentials)
                        exit = True
                        break
        
    return                


def individualFunctions(credentials:list):
    root = credentials[0]
    nsmap = credentials[1]
    url = credentials[2]
    user = credentials[3]
    password = credentials[4]

    logger.setLevel(logging.DEBUG)    

    order = createOrder(root, nsmap, url, user, password, logger)
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
                    9: "Due Dates", 
                    10: "Action Codes", 
                    11: "Type Codes",
                    12: "Product Instance IDs", 
                    13: "Submit Order"}
        

        menu(choices.values(), firstCall=True)
        pick = ensureValidChoice("What value would you like to replace?: ", len(choices))

        if pick == 0:
            break
        else:
            if pick >= 9:
                if pick == 9:
                    dueDateReplace(root, nsmap)
                elif pick == 10:
                    print("Please provide the desired action code: ")
                    value = input(">> ")
                    order.changeActionCodes(order.root, value.capitalize())
                elif pick == 11:
                    print("Please provide the desired type code: ")
                    value = input(">> ")
                    order.changeTypeCodes(order.root, value.capitalize())
                elif pick == 12:
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
    order = createOrder(root, nsmap, url, user, password, logger)

    order.orderIdReplace()
    order.changeActionCodes(order.root, "PR")

    outputFn = order.getOutputFilename()

    with open("%s.xml" % outputFn, 'wb') as file:
        print(f"\nOutput Filename: {outputFn}.xml")
        file.write(etree.tostring(order.root))





def main():
    nsmap={'x': 'http://www.w3.org/2001/XMLSchema-instance', 'ng': 'http://ngpp.fulfilment.services.rogers.com', 'a': 'http://fulfilment.services.cust.oms.amdocs.com'}
    user = "admin"
    password = "welcome1"

    # Change logging level to DEBUG for verbose output
    logging.basicConfig(level=logging.INFO)
    options(nsmap, user, password)
    # testing()

if __name__ == '__main__':
    main()