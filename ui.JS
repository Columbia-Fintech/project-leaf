var num = 1; // filter number
const elmtsCheck = new Map(); // map of filter elements

function addFilter(){ // adds filter form elements 
    $(".additional").append(
        "<div id='div" + num + "'>" +
            "<label>Field:&nbsp;</label>" +
            "<select name='field" + num + "' id='field" + num + "'>" + 
                "<option value=''></option>" +
                "<option value='cal'>Calcium</option>" + 
                "<option value='iron'>Iron</option>" + 
                "<option value='sod'>Sodium</option>" + 
                "<option value='va'>Vitamin A</option>" + 
                "<option value='vc'>Vitamin C</option>" + 
                "<option value='chol'>Cholesterol</option>" + 
                "<option value='sat'>Total Saturated Fat</option>" + 
                "<option value='prot'>Protein</option>" + 
                "<option value='carb'>Carbohydrate</option>" + 
                "<option value='eneg'>Energy</option>" + 
                "<option value='sug'>Sugars</option>" + 
                "<option value='fib'>Fiber</option>" + 
                "<option value='pot'>Potassium</option>" + 
                "<option value='trans'>Total Trans Fat</option>" + 
                "<option value='fat'>Total Fat</option>" + 
            "</select>" +
            "<label>&nbsp;&nbsp;Daily Value:&nbsp;</label>" +
            "<input type='text' id='amt" + num + "' name='amt" + num + "' placeholder='(% Daily Value)'> &nbsp;&nbsp; " + 
            "<select name='ltm" + num + "' id='ltm" + num + "'>" + 
                "<option value=''></option>" +
                "<option value='less'>Less Than</option>" + 
                "<option value='more'>More Than</option>" + 
            "</select>" +
            "<button class='xbutton' id='but" + num + "' type='button' onclick='removeFilter("+ num +")'> &nbsp;&nbsp; x &nbsp;&nbsp;</button> <br><br>" +
        "</div>"  
    );
    
    elmtsCheck.set( num, ["field"+num ,"amt"+num,"ltm"+num] );
    num++;
}

function removeFilter(t){ // removes the filter when users click X button, uses num variable as element identifier 
    let i = "#div" + t;
    // console.log(i);
    $(i).remove();
    elmtsCheck.delete(t)
    // console.log("clicked");
}

function check(){ // ensures all filter fields are filled in 
    // console.log("enter check");
    if(elmtsCheck.size > 0){
        const i = elmtsCheck.entries();
        // console.log(i);
        for (const [key, value] of i){
            // console.log(document.forms["form"]["field1"].value);
            let s1 = document.forms["form"][value[0]].value;
            let s2 = document.forms["form"][value[1]].value;
            let s3 = document.forms["form"][value[2]].value;
            // console.log(s1);console.log(s2);console.log(s3);
            if( !s1 || !s2 || !s3){
                alert("Make sure all fields are filled or deleted!");
                return false;
            }
        }
    }
    
    return true;
}

function submitS(){ // takes all input in fields and formats them to send to getdatabasefood endpoint, response data display -> display()
    
    //form data dictionary     
    var elmt = {};
    elmt.fdcid = document.forms["form"]["name"].value || "";
    // elmt.brand = document.forms["form"]["brand"].value || "";
    elmt.ingd = document.forms["form"]["ingd"].value || "";
    elmt.cat = document.forms["form"]["cat"].value || "";
    
    var tempList = [];

    if(elmtsCheck.size > 0){
        const i = elmtsCheck.entries();
        // console.log(i);
        for (const [key, value] of i){
            let temp = {};

            let s1 = document.forms["form"][value[0]].value;
            let s2 = document.forms["form"][value[1]].value;
            let s3 = document.forms["form"][value[2]].value;

            temp.field = s1;
            temp.amt = s2;
            temp.ltm = s3;

            tempList.push(temp);
        }
    }
    

    ds = {
        "main": elmt,
        "addFields": tempList
    }
    console.log(ds);
    //send post request
    $.ajax({
        type: "POST",
        url: "http://127.0.0.1:5000/getdatabasefood",
        data: JSON.stringify(ds),
        success: function (response){
            // console.log(response);
            if(!Object.keys(response).length){
                console.log("no data")
            } else{
                display(response);
            }
        },
        contentType: 'application/json',
        dataType: 'json'
    });
}

// Object mapping returned labels with something a bit more human-friendly
const aliases = {'brandOwner': 'Brand',
    'brandedFoodCategory': 'Category',
    'description': 'Food Item',
    'fdcId': 'ID',
    'ingredients': 'Ingredients',
    'dv': 'Daily Value',
    'nutrientAmount': 'Amount per 200g/ml Serving',
    'nutrientName': 'Nutrient'};

function display(res) { // takes response data and populates main table with food entries and detail button -> modal(fdcid) 
    reset("top10");
    // console.log(res["result"]);

    let l = res["result"];

    //console.log(l[0]);
    let t = l[0];

    const i = Object.entries(t);
    for (const [key, value] of i){
        $("#rowh").append("<th>" + aliases[key] + "</th>");
    }

    $("#rowh").append("<th> Details </th>");

    let temp = 0;

    for(let k=0; k < l.length; k++){
        $("#top10").append("<tr id=row"+temp+"></tr>");
        const j = l[k];
        for (const [key, value] of Object.entries(j)){
           $("#row"+temp).append("<td>" + value + "</td>");
        }
        $("#row"+temp).append("<td><button type='button' onclick='modal(" + l[k]["fdcId"] + ");'> Details </button></td>");
        
        temp++;
    }
}

function modaldisplay(res){ // takes response from endpoint and populates the modal table everytime a user clicks details button
    reset("t-mod");
    
    let l = res["result"][0];

    console.log(l);

    // console.log(l[0]);
    let t = l[0];

    console.log(t);

    const i = Object.entries(t);
    for (const [key, value] of i){
        $("#rowh2").append("<th>" + aliases[key] + "</th>");
    }

    let temp = 0;

    for(let k=0; k < l.length; k++){
        $("#t-mod").append("<tr id=rowz"+temp+"></tr>");
        const j = l[k];
        for (const [key, value] of Object.entries(j)){
           $("#rowz"+temp).append("<td>" + value + "</td>");
        }
        temp++;
    }

}

function modal(id){ // when details button is clicked, sends fdcid to getdatabasenutrient endpoint and receive modal info (modaldisplay())
    // send text input and retrive data
    console.log("id" + id);
    $.ajax({
        type: "POST",
        url: "http://127.0.0.1:5000/getdatabasenutrient",
        data: JSON.stringify({"main": {"fdcid": id}}),
        success: function (response){
            console.log(response);
            if(!Object.keys(response).length){
                console.log("no data")
            } else{
                modaldisplay(response);
            }
            //console.log(response);
        },
        contentType: 'application/json',
        dataType: 'json'
    });
    // make modal visible
    $(".modal").css("display", "");
    $(".main").css("display", "none");
    $("body").css("background-color", "#00000067");
}

function reset(id){ // resets and clears the data table everytime a new form is submitted or detail button is pressed
    if (id == "t-mod"){
        $("#" + id).remove();
        $("#mod").append("<table id='t-mod'><tr id='rowh2'></tr></table>");
    } else {
        $("#" + id).remove();
        $("#rep").append("<table id = 'top10'><tr id='rowh'></tr></table>");
    }
}

function exitModal(){ // closes the modal
    $(".modal").css("display", "none");
    $(".main").css("display", "");
    $("body").css("background-color", "white");
}

$(document).ready(function(){

    // modal starts off unseen
    $(".modal").css("display", "none");
    
    // when add button pressed, adds filter fields
    $("#add").click(function(){
        addFilter();
    });
    
    // when form is submitted, goes through input check (check()), then data submitted to backend (submitS())
    $("#form").submit(function(ev){
        ev.preventDefault();
        console.assert(check());
        submitS();
    });
    
});