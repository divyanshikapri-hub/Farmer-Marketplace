// ========================================
// FARMLINK FRONTEND
// ========================================

// Your Flask backend address
const API_URL = "http://127.0.0.1:5000/api";

// Keep track of the current form
let currentForm = "login";
let currentUserId = null;
let currentUserRole = null;
// ========================================
// 1. LOAD AND DISPLAY CROPS
// ========================================

async function loadCrops() {
    const cropList = document.getElementById("cropList");
    const searchInput = document.getElementById("searchInput");
    const searchText = searchInput.value.trim();
    const categoryFilter = document.getElementById("categoryFilter");
    const selectedCategory = categoryFilter.value;
    const minPrice = document.getElementById("minPrice").value;
    const maxPrice = document.getElementById("maxPrice").value; 
 
    cropList.innerHTML = "<p>Loading crops...</p>";

    try {
        const params = new URLSearchParams();
        if (searchText) {
            params.set("search", searchText);
        }
        if (selectedCategory) {
            params.set("category", selectedCategory);
        }
        if (minPrice !== "") {
            params.set("min_price", minPrice);
        }
        if (maxPrice !== "") {
            params.set("max_price", maxPrice);
        }
        let url = `${API_URL}/crops`;
        if (params.toString()) {
            url += `?${params.toString()}`;
        }

        const response = await fetch(url);
        const data = await response.json();

        if (!response.ok) {
            throw new Error("Could not load crops.");
        }

        const crops = data.crops || [];

        if (crops.length === 0) {
            cropList.innerHTML = `
                <p>No crops found. Try another search.</p>
            `;
            return;
        }

        cropList.innerHTML = crops.map(crop => {
            const cropName = escapeHTML(
                crop.crop_name || crop.name || "Unnamed crop"
            );

            const category = escapeHTML(
                crop.category || "Other"
            );

            const price = Number(
                crop.price_per_unit ?? crop.price ?? 0
            );

            const quantity = Number(
                crop.quantity_available ?? crop.quantity ?? 0
            );

            const unit = escapeHTML(crop.unit || "kg");

            const farmer = escapeHTML(
                crop.farmer?.name ||
                crop.farmer_name ||
                "Local farmer"
            );

            const emoji = getCropEmoji(category);

            return `
                <article class="crop-card">
                    <div class="crop-emoji">${emoji}</div>

                    <span class="crop-category">
                        ${category}
                    </span>

                    <h3>${cropName}</h3>

                    <p class="crop-price">
                        ₹${Number.isFinite(price) ? price.toLocaleString("en-IN") : "0"}
                        / ${unit}
                    </p>

                    <p class="crop-detail">
                        Available: ${Number.isFinite(quantity) ? quantity : 0} ${unit}
                    </p>

                    <p class="crop-detail">
                        Farmer: ${farmer}
                    </p>

                    ${currentUserRole === "buyer"
                        ? `<button class="btn-primary" onclick="buyCrop(${Number(crop.crop_id)})">Buy</button>`
                        : `<button class="btn-primary" onclick="showLogin()">Login to Continue</button>`
                    }
                </article>
            `;
        }).join("");

    } catch (error) {
        console.error("Crop loading error:", error);

        cropList.innerHTML = `
            <p>
                Could not connect to the FarmLink server.
                Make sure the Flask backend is running.
            </p>
        `;
    }
}

// Choose an emoji based on the crop category
function getCropEmoji(category) {
    const emojis = {
        grain: "🌾",
        vegetable: "🥕",
        fruit: "🍎",
        pulse: "🫘",
        oilseed: "🌻",
        other: "🌱"
    };

    return emojis[String(category).toLowerCase()] || "🌱";
}

// Prevent crop details from being interpreted as HTML
function escapeHTML(value) {
    return String(value).replace(/[&<>"']/g, character => {
        const replacements = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;"
        };

        return replacements[character];
    });
}

// ========================================
// 2. SHOW LOGIN FORM
// ========================================

function showAddCrop() {
    document.getElementById("accountSection").hidden = true;

    const cropSection = document.getElementById("addCropSection");
    cropSection.hidden = false;
    cropSection.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });
}

async function showMyCrops() {
    const section = document.getElementById("myCropsSection");
    const list = document.getElementById("myCropsList");
    const message = document.getElementById("myCropsMessage");

    document.getElementById("accountSection").hidden = true;
    document.getElementById("addCropSection").hidden = true;

    section.hidden = false;
    section.scrollIntoView({ behavior: "smooth", block: "start" });

    if (!currentUserId) {
        message.textContent = "Please log in again to view your crops.";
        return;
    }

    message.textContent = "Loading your crops...";
    list.innerHTML = "";

    try {
        const response = await fetch(
            `${API_URL}/crops?farmer_id=${encodeURIComponent(currentUserId)}`,
            { credentials: "include" }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || "Could not load your crops.");
        }

        const crops = data.crops || [];

        if (crops.length === 0) {
            message.textContent = "You haven't listed any available crops yet.";
            return;
        }

        message.textContent = `You have ${crops.length} crop listing(s).`;

        list.innerHTML = crops.map(crop => `
            <div class="crop-card">
                <h3>${escapeHTML(crop.crop_name || crop.name || "Crop")}</h3>
                <p>Quantity: ${escapeHTML(String(crop.quantity_available ?? crop.quantity ?? 0))} ${escapeHTML(crop.unit || "kg")}</p>
                <p>Price: ₹${escapeHTML(String(crop.price_per_unit ?? crop.price ?? 0))} per unit</p>
                <p>Category: ${escapeHTML(crop.category || "Other")}</p>
                <button 
                    class="btn-primary"
                    onclick="editCrop(${Number(crop.crop_id ?? crop.id)})">
                    Edit
                </button>
                <button
                    class="btn-outline"
                    onclick="deleteCrop(${Number(crop.crop_id ?? crop.id)})">
                    Delete
                </button>
            </div>
        `).join("");

    } catch (error) {
        console.error("My Crops error:", error);
        message.textContent = error.message;
    }
}

async function editCrop(cropId) {
    const newPrice = prompt("Enter the new price per unit (₹):");
    if (newPrice === null) return;

    const price = Number(newPrice);
    if (!Number.isFinite(price) || price <= 0) {
        alert("Please enter a price greater than zero.");
        return;
    }

    const newQuantity = prompt("Enter the new available quantity:");
    if (newQuantity === null) return;

    const quantity = Number(newQuantity);
    if (!Number.isFinite(quantity) || quantity < 0) {
        alert("Please enter a valid quantity (zero or more).");
        return;
    }

    try {
        const response = await fetch(`${API_URL}/crops/${cropId}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({
                price_per_unit: price,
                quantity_available: quantity
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || "Could not update the crop.");
        }

        alert("Crop updated successfully!");
        await showMyCrops();
        await loadCrops();

    } catch (error) {
        console.error("Edit crop error:", error);
        alert(error.message);
    }
}

async function deleteCrop(cropId) {
    const confirmed = confirm(
        "Are you sure you want to remove this crop from the marketplace?"
    );

    if (!confirmed) return;

    try {
        const response = await fetch(`${API_URL}/crops/${cropId}`, {
            method: "DELETE",
            credentials: "include"
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || "Could not delete the crop.");
        }

        alert("Crop removed from the marketplace successfully!");

        await showMyCrops();
        await loadCrops();

    } catch (error) {
        console.error("Delete crop error:", error);
        alert(error.message);
    }
}


function showLogin() {
    currentForm = "login";

    document.getElementById("accountSection").hidden = false;
    document.getElementById("formTitle").textContent =
        "Login to FarmLink";

    document.getElementById("nameField").hidden = true;
    document.getElementById("phoneField").hidden = true;
    document.getElementById("roleField").hidden = true;

    document.getElementById("email").required = true;
    document.getElementById("password").required = true;

    document.getElementById("email").type = "email";
    document.getElementById("email").placeholder = "Enter your email";

    document.getElementById("switchMessage").textContent =
        "New to FarmLink?";

    document.getElementById("switchButton").textContent =
        "Create an account";

    document.getElementById("formMessage").textContent = "";
    document.getElementById("accountForm").reset();
}

// ========================================
// 3. SHOW REGISTRATION FORM
// ========================================

function showRegister() {
    currentForm = "register";

    document.getElementById("accountSection").hidden = false;
    document.getElementById("formTitle").textContent =
        "Create your FarmLink account";

    document.getElementById("nameField").hidden = false;
    document.getElementById("phoneField").hidden = false;
    document.getElementById("roleField").hidden = false;

    document.getElementById("name").required = true;
    document.getElementById("phone").required = true;
    document.getElementById("district").required = true;
    document.getElementById("state").required = true;

    document.getElementById("switchMessage").textContent =
        "Already have an account?";

    document.getElementById("switchButton").textContent =
        "Login instead";

    document.getElementById("formMessage").textContent = "";
    document.getElementById("accountForm").reset();
}

// ========================================
// 4. CLOSE ACCOUNT FORM
// ========================================

function hideAccount() {
    document.getElementById("accountSection").hidden = true;
}

// ========================================
// 5. SWITCH BETWEEN LOGIN AND REGISTER
// ========================================

document.getElementById("switchButton").addEventListener("click", () => {
    if (currentForm === "login") {
        showRegister();
    } else {
        showLogin();
    }
});

// ========================================
// 6. LOGIN AND REGISTRATION
// ========================================

document.getElementById("accountForm").addEventListener(
    "submit",
    async function (event) {
        event.preventDefault();

        const message = document.getElementById("formMessage");
        const submitButton = document.querySelector(".form-submit");

        message.textContent = "Please wait...";
        submitButton.disabled = true;

        try {
            let endpoint;
            let payload;

            if (currentForm === "login") {
                endpoint = "/login";

                payload = {
                    email: document.getElementById("email").value.trim(),
                    password: document.getElementById("password").value
                };
            } else {
                endpoint = "/register";

                payload = {
                    name: document.getElementById("name").value.trim(),
                    email: document.getElementById("email").value.trim(),
                    password: document.getElementById("password").value,
                    phone: document.getElementById("phone").value.trim(),
                    role: document.getElementById("role").value,
                    district: document.getElementById("district").value.trim(),
                    state: document.getElementById("state").value.trim()
                };
            }

            const response = await fetch(`${API_URL}${endpoint}`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                credentials: "include",
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data.error || data.message || "The request failed."
                );
            }

            if (currentForm === "login") {
                message.textContent = "Login successful! Welcome to FarmLink.";
                message.style.color = "green";
                const userName = data.user?.full_name || data.user?.name || "User";
                currentUserId = data.user?.user_id || data.session?.user_id || null;
                const userRole = data.user?.role || data.session?.role || "";
                currentUserRole = userRole;
                const addCropButton = (userRole === "farmer" || userRole === "admin")
                    ? `<button class="btn-primary" onclick="showAddCrop()">Add Crop</button>`
                    : "";
                const myCropsButton = userRole === "farmer"
                    ? `<button class="btn-outline" onclick="showMyCrops()">My Crops</button>`
                    : "";
                const myOrdersButton = userRole === "buyer"
                ? `<button class="btn-outline" onclick="showMyOrders()">My Orders</button>`
                : "";
                document.getElementById("navButtons").innerHTML = `
                    ${addCropButton}
                    ${myCropsButton}
                    ${myOrdersButton}
                    <div class="user-welcome">
                        <div class="user-avatar">👤</div>
                        <div class="user-info">
                            <span class="user-label">SIGNED IN AS</span>
                            <strong>${escapeHTML(userName)}</strong>
                        </div>
                    </div>
                    <button class="btn-outline" onclick="logout()">Logout</button>
                `;
                await loadCrops();
                setTimeout(() => {
                    hideAccount();
                }, 1200);

            } else {
                message.textContent =
                    "Registration successful! You can now log in.";
                message.style.color = "green";

                setTimeout(() => {
                    showLogin();
                }, 1500);
            }

        } catch (error) {
            console.error("Account error:", error);

            message.textContent =
                error.message ||
                "Unable to connect. Check whether the backend is running.";

            message.style.color = "red";

        } finally {
            submitButton.disabled = false;
        }
    }
);

// ========================================
// 7. LOAD CROPS WHEN THE PAGE OPENS
// ========================================

document.addEventListener("DOMContentLoaded", loadCrops);
async function logout() {
    try {
        await fetch(`${API_URL}/logout`, {
            method: "POST",
            credentials: "include"
        });
    } catch (error) {
        console.error("Logout error:", error);
    }

    document.getElementById("navButtons").innerHTML = `
        <button class="btn-outline" onclick="showLogin()">Login</button>
        <button class="btn-primary" onclick="showRegister()">Register</button>
    `;
}

document.getElementById("addCropForm").addEventListener("submit", async function (event) {
    event.preventDefault();

    const message = document.getElementById("cropFormMessage");
    const submitButton = this.querySelector('button[type="submit"]');

    message.textContent = "Saving your crop...";
    message.style.color = "green";
    submitButton.disabled = true;

    const payload = {
        crop_name: document.getElementById("cropName").value.trim(),
        category: document.getElementById("cropCategory").value,
        quantity_available: Number(document.getElementById("cropQuantity").value),
        unit: document.getElementById("cropUnit").value,
        price_per_unit: Number(document.getElementById("cropPrice").value),
        harvest_date: document.getElementById("cropHarvestDate").value,
        description: document.getElementById("cropDescription").value.trim()
    };

    try {
        const response = await fetch(`${API_URL}/crops`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            credentials: "include",
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || data.error || "Could not add crop.");
        }

        message.textContent = "Crop added successfully!";
        message.style.color = "green";

        document.getElementById("addCropForm").reset();
        await loadCrops();

    } catch (error) {
        console.error("Add crop error:", error);
        message.textContent = error.message;
        message.style.color = "red";
    } finally {
        submitButton.disabled = false;
    }
});
let selectedCropId = null;

function buyCrop(cropId) {
    selectedCropId = cropId;

    document.getElementById("accountSection").hidden = true;
    document.getElementById("addCropSection").hidden = true;
    document.getElementById("myCropsSection").hidden = true;

    const checkoutSection = document.getElementById("checkoutSection");
    checkoutSection.hidden = false;

    document.getElementById("checkoutItems").innerHTML =
        `<p>Crop selected. Enter your delivery address below to continue.</p>`;

    document.getElementById("checkoutMessage").textContent = "";

    checkoutSection.scrollIntoView({ behavior: "smooth" });
}
function showMyOrders() {
    document.getElementById("accountSection").hidden = true;
    document.getElementById("addCropSection").hidden = true;
    document.getElementById("myCropsSection").hidden = true;
    document.getElementById("checkoutSection").hidden = true;
    document.getElementById("myOrdersSection").hidden = false;

    document.getElementById("myOrdersMessage").textContent = "";
    document.getElementById("myOrdersList").innerHTML = "";

    loadMyOrders();

    document.getElementById("myOrdersSection").scrollIntoView({
        behavior: "smooth"
    });
}
document.getElementById("checkoutForm").addEventListener("submit", async function (event) {
    event.preventDefault();

    const checkoutMessage = document.getElementById("checkoutMessage");
    const shippingAddress = document.getElementById("shippingAddress").value.trim();
    const paymentMethod = document.getElementById("paymentMethod").value;

    if (!currentUserId || currentUserRole !== "buyer") {
        checkoutMessage.textContent = "Please log in as a buyer to place an order.";
        return;
    }

    if (!selectedCropId) {
        checkoutMessage.textContent = "Please select a crop first.";
        return;
    }

    checkoutMessage.textContent = "Placing your order...";

    try {
        const quantity = Number(prompt("How many units would you like to buy?"));

        if (!Number.isFinite(quantity) || quantity <= 0) {
            checkoutMessage.textContent = "Please enter a valid quantity.";
            return;
        }

        const response = await fetch(`${API_URL}/orders`, {
            method: "POST",
            credentials: "include",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                shipping_address: shippingAddress,
                payment_method: paymentMethod,
                items: [{
                    crop_id: selectedCropId,
                    quantity: quantity
                }]
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || data.error || "Could not place the order.");
        }

        document.getElementById("checkoutForm").reset();
        selectedCropId = null;
        document.getElementById("checkoutSection").hidden = true;
        document.getElementById("accountSection").hidden = true;
        document.getElementById("addCropSection").hidden = true;
        document.getElementById("myCropsSection").hidden = true;
        document.getElementById("myOrdersSection").hidden = true;
        document.getElementById("confirmationOrderId").textContent =
        `Your order number is: ${data.order?.order_id ?? data.order?.id ?? "confirmed"}`;
        document.getElementById("orderConfirmationSection").hidden = false;
        await loadCrops();
        document.getElementById("orderConfirmationSection").scrollIntoView({
            behavior: "smooth"
        });
    } catch (error) {
        checkoutMessage.textContent = error.message || "Something went wrong.";
    }
});
async function loadMyOrders() {
    const ordersList = document.getElementById("myOrdersList");
    const ordersMessage = document.getElementById("myOrdersMessage");

    if (!currentUserId || currentUserRole !== "buyer") {
        ordersMessage.textContent = "Please log in as a buyer to view your orders.";
        return;
    }

    ordersMessage.textContent = "Loading your orders...";

    try {
        const response = await fetch(`${API_URL}/orders`, {
            method: "GET",
            credentials: "include"
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || data.error || "Could not load your orders.");
        }

        const orders = Array.isArray(data)
            ? data
            : (data.orders || []);

        if (orders.length === 0) {
            ordersList.innerHTML = "<p>You haven't placed any orders yet.</p>";
            ordersMessage.textContent = "";
            return;
        }

        ordersList.innerHTML = orders.map(order => `
        <article class="crop-card">
        <h3>Order #${escapeHTML(String(order.order_id ?? "—"))}</h3>
        <p>Status: ${escapeHTML(String(order.status ?? "Pending"))}</p>
        <p>Order date: ${escapeHTML(String(order.order_date ?? "—"))}</p>
        <h4>Items ordered</h4>
        ${
            Array.isArray(order.items) && order.items.length > 0
                ? `<ul>
                    ${order.items.map(item => `
                        <li>
                            ${escapeHTML(String(item.crop_name ?? "Unknown crop"))}
                            — ${escapeHTML(String(item.quantity ?? 0))}
                            ${escapeHTML(String(item.unit ?? "kg"))}
                            × ₹${escapeHTML(String(item.unit_price ?? 0))}
                            = ₹${escapeHTML(String(item.subtotal ?? 0))}
                        </li>
                    `).join("")}
                   </ul>`
                : "<p>Item details are unavailable.</p>"
        }

        <p><strong>Order total: ₹
    ${escapeHTML(String(order.total_amount ?? 0))}</strong></p>
    </article>
    `).join("");

        ordersMessage.textContent = "";
    } catch (error) {
        ordersMessage.textContent = error.message || "Something went wrong while loading orders.";
    }
}
function backToMarketplace() {
    document.getElementById("checkoutSection").hidden = true;
    document.getElementById("orderConfirmationSection").hidden = true;
    document.getElementById("accountSection").hidden = true;
    document.getElementById("addCropSection").hidden = true;
    document.getElementById("myCropsSection").hidden = true;
    document.getElementById("myOrdersSection").hidden = true;

    document.getElementById("crops").scrollIntoView({
        behavior: "smooth"
    });
}