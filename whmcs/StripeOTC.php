<?php
////////////////////////////////////////////////////
// WHMCS Payment gateway module for Stripe Checkout 
//
// Copyright (C) 2023 Nicholas Yoannou
//
// License:  Under GitHub repository (nicholasyoannou/stripe-checkout-whmcs) README file.
// https://nicholas.dev
// Contact: nicholas@nicholas.dev
// Version 1
////////////////////////////////////////////////////

if (!defined( "WHMCS" )) {
	exit( "This file cannot be accessed directly" );
}

function StripeOTC_MetaData()
{
    return [
        'DisplayName' => 'Stripe One Time Checkout'
    ];
}

function StripeOTC_config() {
    $configarray = array(
     "FriendlyName" => array("Type" => "System", "Value"=>"Stripe - One-Time"),
     );
	return $configarray;
}

function StripeOTC_link($params) {
	return '<form method="post" action="INSERT_YOUR_API_URL_HERE_INCLUDING_HTTPS_OR_HTTP_PART/makePaymentInvoice" enctype="application/x-www-form-urlencoded">
        <input type="hidden" name="invoice_number" value="' . $params['invoiceid'] . '" />
        <input type="hidden" name="description" value="' . $params['description'] . '" />
        <input type="hidden" name="amount" value="' . $params['amount'] . '" />
        <input type="hidden" name="currency" value="' . $params['currency'] . '" />
		<input type="hidden" name="customeremail" value="' . $params['clientdetails']['email'] . '" />
        <input id="stripe_checkout_custom" type="submit" onclick="this.disabled=true;this.form.submit();" value="' . $params['langpaynow'] . '" />
        </form>
        ';
}
