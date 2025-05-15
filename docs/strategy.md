# Strategy

## Step 1: Define Your Strategy
In order to maximize profitability, we need to focus on maximizing our shop's reputation, which relies on these four things:
- Value: Pricing not too high so customers will choose your shop over others, but not too low so you still make a profit
- Quality: Choosing specific potion mixes based on the customers' classes
- Reliability: Making sure the shop always has the right potions in stock
- Recognition: Making sure that all purchases are successful and nothing fails
Each of my three key changes to the potion shop will focus on a different factor in the shop's reputation.

### Hypothesis 1: Optimizing Value
I will implement a pricing model that makes use of supply and demand to see what price is optimal for customers. Currently, the pricing is static, however this pricing model will change based on how much customers buy our potions. For instance, if a certain potion is bought a lot, then the price will increase until the potion is not bought enough. Inversely, potions that are high in inventory should be given a discount in order to encourage customers to buy them. Ideally, the prices will constantly be changing based on the current market. This change matters because the price is what determines whether a customer buys the potion, so instead of having a static price we should have a price that is constantly around the optimal value.

### Hypothesis 2: Optimizing Quality
This factor will be optimized based off of the customer's preferences. There will be a model added that will look at the customers' classes, and based off of the largest amount of classes, certain potion mixes will be made more. For instance, if a certain class of customers likes potion mix X and that class of customers comes more during a certain time of the day, that potion mix will be made more during that time of the day. In short, the potion mixes will be determined based on the customers' classes. This change matters because the customers will choose what potions to buy not only based off of price, but also based off of their own personal preferences, so there would be a higher chance of more potions being sold if we had the right potion mixes being sold.

### Hypothesis 3: Optimizing Reliability and Recognition
Both reliability and recognition will be improved by making sure the right potions are always in stock. This will be done by pre-brewing potions based off of past sales. This is different from hypothesis 2 because instead of optimizing price by looking at what potions customers buy, we are reducing the chance of stockouts by looking at past sales. The data taken from this model and the data taken from hypothesis 2's model will be combined to make a more efficient store. This change matters because instead of optimizing price, it also prevents stockout, which both prevents failed sales (which makes more money) and increases the recognition of the store, which will make customers more likely to return.

## Step 2: Design Your Experiments

### Hypothesis 1:
How to measure success: Whether or not a certain potion type is bought a lot
How to measure effects over time: Track average profit by potion type to see what potion mixes are doing well and need a change in price

### Hypothesis 2:
How to measure success: Whether or not a certain customer class is buying potions a lot
How to measure effects over time: Track whether or not customers are buying potions a lot by class

### Hypothesis 3:
How to measure success: Whether or not past sales ever had any stockouts
How to measure effects over time: Track how many stockouts there have been over time

## Step 3: Implement Additional Instrumentation

### Hypothesis 1: Based off of potion sales
Recorded each time potion is bought:
- Timestamp
- Potion ID
- Potion Price
- Potion Recipe
- Total quantity sold
- Total gold earned
- Number of potions in inventory

This instrumentation records information on the potion price and how the inventory is doing in order to record how well the type of potion is doing in sales based off of how much it is sold.

### Hypothesis 2: Based off of customer classes
Recorded each time potion is bought:
- Timestamp
- Potion ID
- Potion Price
- Potion Recipe
- Customer Class
- Customer ID

This instrumentation records information on the customer class in order to see what types of potions the customers are buying so we can see what potions certain types of customers like.

### Hypothesis 3: Based off of past sales
From purchasing logs
- Potions Expired/Unsold
- Stockouts

This instrumentation takes information from the purchasing logs about how many potions have expired or were not sold and stockouts. This is too see what potions we need less of or more of.

## Step 4: Write Analytic Queries

### Hypothesis 1:
SELECT<br>
&nbsp;&nbsp;&nbsp;&nbsp;PotionID,<br>
    DATE(Timestamp) AS SaleDate,<br>
    SUM(TotalQuantitySold) AS TotalQuantitySold,<br>
    SUM(TotalGoldEarned) AS TotalGoldEarned,<br>
    AVG(PotionPrice) AS AvgPotionPrice,<br>
    AVG(NumberOfPotionsInInventory) AS AvgInventory<br>
FROM PotionSales<br>
GROUP BY PotionID, DATE(Timestamp)<br>
ORDER BY SaleDate, PotionID;<br>


### Hypothesis 2:
SELECT<br>
    CustomerClass,<br>
    PotionID,<br>
    COUNT(*) AS NumPurchases,<br>
    SUM(PotionPrice) AS TotalSpent<br>
FROM PotionPurchases<br>
GROUP BY CustomerClass, PotionID<br>
ORDER BY CustomerClass, NumPurchases DESC;<br>

### Hypothesis 3:
SELECT<br>
    PotionID,<br>
    DATE(LogDate) AS Date,<br>
    SUM(CASE WHEN EventType = 'Stockout' THEN 1 ELSE 0 END) AS Stockouts,<br>
    SUM(CASE WHEN EventType = 'Expired' THEN 1 ELSE 0 END) AS ExpiredPotions<br>
FROM InventoryLogs<br>
GROUP BY PotionID, DATE(LogDate)<br>
ORDER BY Date, PotionID;<br>
