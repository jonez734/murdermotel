<?php

require_once("config.php");

require_once("engine.php");
require_once("session.php");
require_once("database.php");

require_once("zoid6.php");

class index
{
  function main()
  {
    \bbsengine6\session\start();
    
    \bbsengine6\setcurrentsite(defined('\config\SITENAME') ? \config\SITENAME : "NEEDINFO");
    \bbsengine6\setcurrentpage("index");
    \bbsengine6\setcurrentaction("view");
    \bbsengine6\setreturnto(\bbsengine6\getcurrenturi());

    $data = [];
    $data["metadata"] = [];
    $data["pagetemplate"] = "index.tmpl";

    $choices = [];
    $data["choices"] = \zoid6\buildchoices($choices);

    \bbsengine6\displaypage($data, "index.tmpl");
    return;
  }
};

$a = new index();
$b = $a->main();
if (PEAR::isError($b))
{
  logentry("index.100: " . $b->toString());
  displayerrorpage($b->getMessage());
  exit;
}
?>
