# Welcome to Linky

> A package for your electrical data analysis from Linky meters

This project provides an overview of your own electrical data from Linky meters (smart meters deployed nationwide in France by French power grid operator Enedis). This project is built with python and can be easily deployed on your own data.

## :hourglass_flowing_sand: How to install

Clone the repository and install dependencies by using poetry as following :
```
poetry install
```

## :zap: How to work with your own data ?

Linky meter data is retrieved using the `MyElectricalData` API. This is a gateway to the official Enedis API (which is not accessible to private individuals without a SIRET number). 

Once you have given your consent, this will generate a personal key (Access Token) needed to authenticate yourself on the API. 

You will then be asked for two information items:
* `access_token`: the Access Token generated above
* `usage_point_id`: your PLD number, which can be found on your invoice from your supplier.

## How to use this library ?

User parameters (defined just above) must be defined in a Yaml file. This file must be named `parameters.yml` and placed in the `src` folder of the library.

Example of a Yaml file `parameters.yml`:

```yaml
api_enedis:
  access_token: "yyyy"
  usage_point_id: "xxxx"
```

## How to use the Dashboard ?

:construction: Coming soon ...
