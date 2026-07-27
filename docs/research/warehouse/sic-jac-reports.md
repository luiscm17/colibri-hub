---
document_type: research
status: active
implementation: not-started
scope: warehouse/reports
authority: evidence
owner: product
last_reviewed: 2026-07-27
---

# SISTEMA SIC JAC 1

## REPORTES

Los reportes estan estructurados por 7 secciones:

* Codigo
Es el numero de item asignado

* Descripcion
Informacion detallada acerca de la categoria/sub categoria/item dependiendo del tipo de reporte solicitado

* Unidad
La unidad de medida usada para el producto (Kilos, litros o  Bolivianos dependiendo del tipo de item manejado)

* Saldo (Un dia anterior al inicio del reporte)
Es todo el stock almacenado antes de la fecha inicio del reporte, consta de dos partes.
Cantidad:
Indica la cantidad almacenada del producto en kilos
Valor:
Es el precio general del lote expresado en Bolivianos

* Entrada
Son todos los productos añadidos a la fecha desde la fecha inicio del reporte que consta igual de la cantidad y el valor

* Salida
Son los productos vendidos hasta la ultima fecha del reporte que consta igual de la cantidad y el valor del lote en general

* Saldos
Es el Stock al ultimo dia del reporte, los preductos que sobraron o no se vendieron

### Formula

(Saldo (Un dia anterior al inicio del reporte) + Entrada) - Salidas = Saldos

Los reportes estan divididos en tres categorias:

* Categoria

Es el reporte mas general posible que abarca muy poco detalle ej: 'Almacen producto terminado'

* Sub categorias

Es el reporte un poco mas detallado que incluye las categorias dentro de 'Almacen producto terminado' ej: 'Titulo 2/18' 'Recuperado' 'Mixto' 'Alpaca' etc

* Item

Es el reporte mas detallado generado el cual incluye y se centra en cada item vendido divido en categoria sub categoria y dando informacion del item en especifico ej: 'Rojo 3006' 'Negro 5000'

#### ENTRADAS

En el apartado de entradas es en donde se hace la añadidura del producto en base al Stock:

* Numero de lote

* Un numero de entrada (Generada por sistema)

* Una descripcion del item (Mayormente nombre del producto especifico)

* La fecha en la que el producto fue ingresado

* Numero de nota (Numero de facturacion)

* Fuente (De donde proviene el producto)

* Proveedor (Illampu Textiles (Fijo))

* Concepto (Depende si el producto esta ingresando recien o es una devolucion)

* Autorizado por (El nombre del responsable(Ing. Bernardo))

* Entregado a (Einard Lopez (Fijo))

##### INGRESO

En el apartado de ingresos se hace la añadidura de un nuevo item:

* Codigo (El numero de lote ej:01-26-47 (El primer numero es el numero de camion del distribuidor, el segundo numero es la gestion, el tercer numero es el numero de ingreso))

* Categoria (Es a la categoria a la que pertenece el item (Tipos de Categoria: Almacen producto terminado, devolucion de lotes))

* Sub Categoria (tipos de titulo: titulo 2/18, alpaca, recuperado, mixto)

* Descripcion (Es el item en especifo si es lana por ('Rojo 3006 2/18' 'Verde Botella 4057 2/32' 'Maiz6005 Recuperado' 'Naranja 1013 2/18 TIPO N'))

* Unidad
Se refiere a la unidad de medida (Kilos)

#### SALIDA

En aqui se marca el objetivo como vendido, especificando cuanto del producto se vendio y cuanto aun queda en el stock este se divide por mas categorias como ser:

* N. Salida (Puesto por el sistema, es un contador que va registrando las salidas y cada vez que hace una se agrega un numero mas)

* N. Nota (Se saca del talonario, es el numero de factura propio de la fabrica que se da a los clientes)

* Fecha (La fecha de salida)

* Tipo de cambio (Es el cambio de dolar a boliviano (6.96))

* Tipo de salida (Salida externa (Este apartado es fijo))

* Destino (El nombre del cliente al cual se le esta entregando)

* Autorizado por: (La persona que esta a cargo y supervisando la salida)

* Concepto (Como se efectuo la salida)

* Entregado a: (El lugar en donde llegara la mercaderia)

Nota: El ingreso es por el numero de lote, el producto se llena automaticamente, la cantidad de entrada/salida se llena automaticamente y se añade o extrae automaticamente al stock

## Tipos de categoria

* Almacen Producto Terminado
* Devoluciones Producto Terminado

## Tipos de Sub Categoria

* Titulo 2/18, 2/32, 4/9, etc..
* Titulos con tipo N (Son los mismos titulos, se diferencian cuando se el tipo de fibra N)
* Titulo n/n CH (Los titulos que tienen la terminacion CH son titulos que indican que el producto terminado es fino)
* Madejitas (Son titulos para Productos en una presentacion diferente conocidos como 'Madejitas')
* Alpaca (Son para productos que se juntan con HB y fibra de Alpaca)
* Mixto = Recuperado
* Titulo Fantasia (Es como el titulo 2/18 pero su peso varia)
* StolL (Es como el 2/32 pero mas fino)

## Nomenclaturas especiales de items

* Terminacion en -D (Devolucion)
* Terminacion en -FT (Fuera de Tabla)
* Terminacion en -VARR (Lote con Varrilla)
* Terminacion en -SN (Semi mate N)
* Terminacion en -Dev (Devolucion)
