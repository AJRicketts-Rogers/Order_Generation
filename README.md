# Order Generation and Submission Tool

This python3 script takes a OMS order as input and changes the required fields to randomly generated values for use in a new order. Supports bulk order submission or file generation.

---

## 🚀 Features

* Generate or modify XML orders with randomized but valid identifiers.
* Submit single or multiple orders to specified OSM endpoints.
* Replace specific XML element values like Order ID, CBP, HHID, MAC address, and more.
* Support for multiple order types including Provide, Change-Owner, Cease, Move (All), and Move (Select).
* Batch submissions with configurable delays and durations.
* Logging and pretty-printed XML output for debugging and auditing.

---

## 📦 Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/AJRicketts-Rogers/Order_Generation.git
   cd Order_Generation
   ```

2. **Install the dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

   **Required packages:**

   * `lxml`
   * `requests`

---

## 🔧 Usage

### Run the program

```bash
python generation.py your_order_file.xml
```

You'll be prompted through a series of menus

---

## 🧽 Function Reference

### From `generation.py`

#### `outputFileRun(credentials, orderType, outputFn='')`

Generates an order file for the given type and writes to XML.

#### `submitRun(credentials, orderType)`

Submits an order and logs the response.

#### `submitMultiple(credentials, numOrders, orderType)`

Submits orders in parallel.

#### `individualFunctions(credentials)`

Allows the user to select which fields to change

#### `dueDateReplace(root, nsmap)`

Gets user input to change all due dates

---

### From `createOrder.py`

#### `createOrder.replaceAll()`

Replaces all significant values in the order (Order IDs, serials, MACs, etc.).

#### `createOrder.submitOrder(url, user, password)`

Submits the current order XML to OSM.

#### `createOrder.getOutputFilename()`

Generates a unique filename using timestamp format.

#### `createOrder.provide()`

Replaces all values and changes the Action and Type codes to PR

#### `createOrder.changeOwner()`

Changes the Action and Type codes to CH, CW, respectively and replaces CBP and Order ID

#### `createOrder.cease()`

Changes the Action and Type codes to CE and replaces CBP and Order ID

#### `createOrder.moveAll()`

Work Pn Progress

#### `createOrder.moveSelect()`

Work In Progress

#### `createOrder.orderItemIdReplace()`

Replaces all relevant order item reference numbers and associated fields.

#### `createOrder.serialReplace()`

Randomizes all serial numbers.

#### `createOrder.macAddressReplace()`

Randomizes MAC addresses..

---


## 🔐 Credentials

These can be modified inside `main()` in `generation.py`.

---
