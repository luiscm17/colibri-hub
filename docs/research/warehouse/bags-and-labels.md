---
document_type: research
status: active
implementation: not-started
scope: warehouse/packaging
authority: evidence
owner: product
last_reviewed: 2026-07-27
---

# BOLSAS Y ETIQUETAS - SIC JAC

En el sistema el apartado de bolsas y etiquetas controla las entradas de los diferentes proveedores para que el producto terminado sea mas facil de identificar, este de igual manera tiene un sistema muy similar de reportes pero manejan diferentes productos que el resto este se divide en las secciones de:

## Sistema de reportes

* Codigo: depende de que se maneje si se maneja categorias se usa el numero de la categoria anteriormente asignada en el sistema como: 'Bolsas', 'Etiquetas', 'Fichas devanado' o 'Talonarios'. La sub categoria igualmente anteriormente asignado en sistema como: 'Bolsa azul 60*95*65', 'Bolsa amarilla 60*95*65'. En el caso del item se coloca su numero de lote o algun diferenciador puesta para cada item
* Descripcion: Describe el producto este dependera de la categoria y la sub categoria, al agregar el item se añade a que categoria pertenece y en que sub categoria se divide
* Unidad: Describe en que unidad se mide si en kilos o piezas mayormente en esta tabla se usan piezas
* Saldo a (Un dia anterior a la fecha inicio del reporte): Es el stock que se tenia antes de iniciar el reporte este se añade a las entradas y se resta con las salidas para tener la informacion de los productos que aun no se vendieron durante el reporte, tiene dos secciones una que indica cuantos productos tiene en existencia (cantidad) y la otra que indica cuanto es el valor monetario de dicha cantidad (valor)
* Entradas: Son todos los productos añadidos durante el reporte que tambien se divide en dos secciones la de la cantidad de porductos añadidos a la fecha (cantidad) y el apartado de el valor de los productos añadidos a la fecha que siempre se expresa en Bolivianos (valor)
* Salidas: Son todos los productos vendidos durante el reporte incluyendo a el stock un dia anterior al reporte y las entradas estas juntas se restan con las salidas y dan una nueva cantidad al stock al final del reporte este tambien se divide en dos secciones la cantidad de productos vendidos (Cantidad) y el valor general de los productos vendidos (Valor)
* Saldos: Es el Stock final que se tiene del reporte este apartado es generado automaticamente con la siguiente formula:
(Saldos a partir de (Fecha de un dia anterior al reporte) + Entradas (Durante el reporte)) - Salidas (Durante el reporte) = Saldos.
Igual esta divido en dos secciones una que indica la cantidad de producto en stock (cantidad) y la otra el valor general de lote (valor)

## Entradas

Es el apartado de confirmacion en la que se indica cuando un producto es añadido y cuanto de este se añade consta de diferentes secciones las cuales son:

* N. Ingreso: Este esta puesto automaticamente por el sistema como un contador de ingresos
* Nota de recepcion: Normalmente se deja en blanco
* Fecha
* T. de cambio: Es el cambio de dolar a bolivianos en el momento
* Fuente (Recursos): Indica de donde estan saliendo los recursos para el producto normalmente 'Recursos propios' Se mantiene fijo
* Tipo de ingreso: Indica a donde se esta ingresando como ser 'Ingreso a almacen' o 'Devolucion a Almacen'
* Proveedor: Indica de donde esta viniendo el producto osea de su proveedor como ser 'Plastic rey', 'Almacen', 'Imprenta illimani', etc..
* Concepto: Un resumen de que esta pasando o como se esta ingresando el producto
* Autorizado por: Es por quien ah sido autrizado a entrar a almacen
* Entregado a: Indica quien es designado para recibir los productos ingresados

## Salidas

Indica los productos ya añadidos al producto final descontando del stock.

* N. Salida: Es puesto automaticamente por el sistema como un contador de salidas
* Nota de entrega: Es el numero de factura puesta por la empresa en su producto
* Fecha
* T. de Cambio
* Tipo de salida: Es el como esta saliendo de almacen puede ser 'Salida de almacen' o 'Devolucion de almacen'
* Destino (cliente): Nombra a quien se entrego el producto
* Concepto: Es un breve resumen de como esta saliendo el producto especificando tambien que esta saliendo
* Autorizado por: Es el encargado de almacen que indica a quien se esta entregando el producto
* Entregado a: Es el responsable de la salida del producto y a quien es derivado

## Ingresos

El apartado de añadidura de un nuevo item o un nuevo tipo de bolsa en este caso esta constituido por:

* Codigo: Indica el numero de bolsa junto a que se refiere como ser 'BLS-01', 'BLS-02', 'ETQ-01', 'ETQ-02'
* Categoria: Indica a donde se esta yendo el item como ser 'Bolsas', 'Etiquetas', 'Fichas devanado' o 'Talonarios'
* Sub Categoria: Dependiendo a la categoria cambia a que sub categoria va a ser añadidad estas se centran mas en el tamaño de la bolsa y sus medidas exactas
* Descripcion: Es una breve descripcion de que es el item llega mas que todo a ser el color o la equiqueta para cierto lote en especifico
* Unidad: es la unidad de medicioen aqui mayormente en aqui se trabajan con piezas

## Categorias manejadas

* Bolsas
* Etiquetas
* Fichas devanado
* Talonarios

## Sub Categorias manejadas

* Bolsas con su respectiva medicion como ser: 'BOLSA ROJO 60*95*65', 'BOLSA PERU 60*95*60', 'BOLSA MADEJITAS 62*105*60', etc..
* Etiquetas y para que lote son usadas como ser: 'Etiquetas colibri bebe', 'Etiquetas colibri dorado', 'Etiquetas colibri dorado', etc..
* Fichas devanado
* Talonarios
