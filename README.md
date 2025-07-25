# Order Generation and Submission Tool

This python3 script takes a OMS order as input and changes the required fields to randomly generated values for use in a new order. Supports bulk order submission or file generation.

---

## 📦 Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/AJRicketts-Rogers/Order_Generation.git
   cd Order_Generation
   ```

2. **Install the dependencies:**

   Make sure you have the latest Microsoft C++ Build Tools installed before running the following command as this is a lxml dependency
   ```https://visualstudio.microsoft.com/visual-cpp-build-tools/```

   See this post for installation instructions
   ```https://stackoverflow.com/questions/64261546/how-to-solve-error-microsoft-visual-c-14-0-or-greater-is-required-when-inst```

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
